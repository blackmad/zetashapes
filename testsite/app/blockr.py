from shapely.geometry import Point, Polygon, MultiPolygon, asShape
from shapely.geometry.polygon import LinearRing
from shapely.ops import cascaded_union, polygonize
from shapely.prepared import prep
from rtree import Rtree
from outliers import discard_outliers
import sys, json, math, pickle, os, geojson
import itertools
from flask import Flask
import flask_gzip
import operator
import json
import re
from functools import wraps
from collections import namedtuple
from flask import redirect, request, current_app, jsonify
import psycopg2
import psycopg2.extras
from collections import defaultdict
import os
from itertools import groupby
from shapely.ops import cascaded_union
from shapely.geometry import mapping, asShape
from shapely import speedups
import geo_utils
import vote_utils
from rtree import Rtree
from shapely.geometry import asShape
import geojson
from shapely import wkb

conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
cur = conn.cursor()

SAMPLE_SIZE = 20
SCALE_FACTOR = 111111.0 # meters per degree latitude
#ACTION_THRESHOLD = 2.0/math.sqrt(1000.0) # 1 point closer than 1km
ACTION_THRESHOLD = 20.0/math.sqrt(1000.0) # 1 point closer than 1km
AREA_BOUND = 0.001
TARGET_ASSIGN_LEVEL = 0.75

areaid = sys.argv[1]
statefp10 = areaid[0:2]
countyfp10 = areaid[2:]

places = {}
names = {}
blocks = {}

do_cache = False

def load_points(nids):
    places = {} 

    cur.execute("""select woe_id, lat, lng FROM flickr_votes WHERE woe_id IN %s""" % (tuple(nids),))
    count = 0
    for row in cur:
        place_id , lat, lon = row
        point = (lat, lon)
        pts = places.setdefault(place_id, set())
        pts.add(point)
        count += 1
        if count % 1000 == 0:
            print >>sys.stderr, "\rRead %d points in %d places." % (count, len(places)),
    print >>sys.stderr, "\rRead %d points in %d places." % (count, len(places))
    return places


if os.path.exists(areaid + '.cache'):
    print >>sys.stderr, "Reading from %s cache..." % areaid
    names, blocks, places = pickle.load(file(areaid + ".cache"))
    blocks = map(asShape, blocks)
else:
    all_names = {}
    count = 0
    cur.execute("""select distinct(label, name) FROM votes v JOIN geoplanet_places ON label::int = woe_id WHERE id LIKE '%s%%'""" % (areaid))
    for row in cur:
        parts = row[0].split(',')
        place_id = parts[0][1:]
        name = (','.join(parts[1:])).replace('"', '').replace(')', '')
        print '%s %s' % (place_id, name)
        all_names[int(place_id)] = name
        count += 1
        if count % 1000 == 0:
            print >>sys.stderr, "\rRead %d names" % count
    print >>sys.stderr, "\rRead %d names" % count

    places = load_points(all_names.keys())
    for place_id in places:
        names[place_id] = all_names.get(place_id, "")
    places = discard_outliers(places)
    
    lines = []
    
    cur.execute("""select geom as geojson_geom FROM tabblock10 tb WHERE statefp10 = %s AND countyfp10 = %s AND blockce10 NOT LIKE '0%%'""", (statefp10, countyfp10))
    for r in cur:
      lines.append(wkb.loads(r[0].decode('hex')))
    blocks = [poly.__geo_interface__ for poly in lines]

if not os.path.exists(areaid + '.cache'):
    if do_cache:
      print >>sys.stderr, "Caching points, blocks, and names ..."
      pickle.dump((names, blocks, places), file(areaid + ".cache", "w"), -1)
    blocks = map(asShape, blocks)

points = []
place_list = set()
count = 0
for place_id, pts in places.items():
    count += 1
    print >>sys.stderr, "\rPreparing %d of %d places..." % (count, len(places)),
    for pt in pts:
        place_list.add((len(points), pt+pt, None))
        points.append((place_id, Point(pt)))
print >>sys.stderr, "Indexing...",
index = Rtree(place_list)
print >>sys.stderr, "Done."

def score_block(polygon):
    centroid = polygon.centroid
    #prepared = prep(polygon)
    score = {}
    outside_samples = 0
    for item in index.nearest((centroid.x, centroid.y), num_results=SAMPLE_SIZE):
        place_id, point = points[item]
        score.setdefault(place_id, 0.0)
        #if prepared.contains(point):
        #    score[place_id] += 1.0
        #else:
        score[place_id] += 1.0 / math.sqrt(max(polygon.distance(point)*SCALE_FACTOR, 1.0))
        outside_samples += 1
    return list(reversed(sorted((sc, place_id) for place_id, sc in score.items())))

count = 0
assigned_blocks = {}
assigned_ct = 0
unassigned = {} #keyed on the polygon's index in blocks
for count in range(len(blocks)):
    polygon = blocks[count]
    print >>sys.stderr, "\rScoring %d of %d blocks..." % ((count+1), len(blocks)),
    if not polygon.is_valid:
        try:
            polygon = polygon.buffer(0)
            blocks[count] = polygon
        except:
            pass
    if not polygon.is_valid:
        continue
    if polygon.is_empty: continue
    if polygon.area > AREA_BOUND: continue

    scores = score_block(polygon)
    best, winner = scores[0]
    if best > ACTION_THRESHOLD:
        assigned_ct += 1
        assigned_blocks.setdefault(winner, [])
        assigned_blocks[winner].append(polygon)
    else:
        # if the block wasn't assigned hang onto the info about the winning nbhd
        unassigned[count] = (best, winner)
print >>sys.stderr, "Done, assigned %d of %d blocks" % (assigned_ct, len(blocks))

new_threshold = ACTION_THRESHOLD
while float(assigned_ct)/len(blocks) < TARGET_ASSIGN_LEVEL and len(unassigned) > 0:
    new_threshold -= 0.1
    print >>sys.stderr, "\rDropping threshold to %f1.3... " % new_threshold
    for blockindex in unassigned.keys():
        best, winner = unassigned[blockindex]
        #if blocks[blockindex].is_empty: del(unassigned[blockindex])
        if best > new_threshold:
            assigned_ct += 1
            assigned_blocks.setdefault(winner, [])
            assigned_blocks[winner].append(blocks[blockindex])
            del unassigned[blockindex]
    print >>sys.stderr, "Done, assigned %d of %d blocks" % (assigned_ct, len(blocks))
    

polygons = {}
count = 0
for place_id in places.keys():
    count += 1
    print >>sys.stderr, "\rMerging %d of %d boundaries..." % (count, len(places)),
    if place_id not in assigned_blocks: continue
    polygons[place_id] = cascaded_union(assigned_blocks[place_id])
print >>sys.stderr, "Done."

count = 0
orphans = []
for place_id, multipolygon in polygons.items():
    count += 1
    print >>sys.stderr, "\rRemoving %d orphans from %d of %d polygons..." % (len(orphans), count, len(polygons)),
    if type(multipolygon) is not MultiPolygon: continue
    polygon_count = [0] * len(multipolygon)
    for i, polygon in enumerate(multipolygon.geoms):
        prepared = prep(polygon)
        for item in index.intersection(polygon.bounds):
            item_id, point = points[item]
            if item_id == place_id and prepared.intersects(point):
                polygon_count[i] += 1
    winner = max((c, i) for (i, c) in enumerate(polygon_count))[1]
    polygons[place_id] = multipolygon.geoms[winner]
    orphans.extend((place_id, p) for i, p in enumerate(multipolygon.geoms) if i != winner)
print >>sys.stderr, "Done."

count = 0
total = len(orphans)
retries = 0
unassigned = None
while orphans:
    unassigned = []
    for origin_id, orphan in orphans:
        count += 1
        changed = False
        print >>sys.stderr, "\rReassigning %d of %d orphans..." % (count-retries, total),
        for score, place_id in score_block(orphan):
            if place_id not in polygons:
                # Turns out we just wind up assigning tiny, inappropriate places
                #polygons[place_id] = orphan
                #changed = True
                continue
            elif place_id != origin_id and orphan.intersects(polygons[place_id]):
                polygons[place_id] = polygons[place_id].union(orphan)
                changed = True
            if changed:
                break
        if not changed:
            unassigned.append((origin_id, orphan))
            retries += 1
    if len(unassigned) == len(orphans):
        # give up
        break
    orphans = unassigned
print >>sys.stderr, "%d retried, %d unassigned." % (retries, len(unassigned))

print >>sys.stderr, "Returning remaining orphans to original places."
for origin_id, orphan in orphans:
    if orphan.intersects(polygons[origin_id]):
        polygons[origin_id] = polygons[origin_id].union(orphan)

print >>sys.stderr, "Try to assign the holes to neighboring neighborhoods."
#merge the nbhds
city = cascaded_union(polygons.values())

#pull out any holes in the resulting Polygon/Multipolygon
if type(city) is Polygon:
    over = [city]
elif type(city) is MultiPolygon:
    over = city.geoms
else:
    print >>sys.stderr, "\rcity is of type %s, wtf." % (type(city))

holes = []
for poly in over:
    holes.extend((Polygon(LinearRing(interior.coords)) for interior in poly.interiors))

count = 0
total = len(holes)
retries = 0
unassigned = None
while holes:
    unassigned = []
    for hole in holes:
        count += 1
        changed = False
        print >>sys.stderr, "\rReassigning %d of %d holes..." % (count-retries, total),
        for score, place_id in score_block(hole):
            if place_id not in polygons:
                # Turns out we just wind up assigning tiny, inappropriate places
                #nbhds[place_id] = hole
                #changed = True
                continue
            elif hole.intersects(polygons[place_id]):
                polygons[place_id] = polygons[place_id].union(hole)
                changed = True
            if changed:
                break
        if not changed:
            unassigned.append(hole)
            retries += 1
    if len(unassigned) == len(holes):
        # give up
        break
    holes = unassigned
print >>sys.stderr, "%d retried, %d unassigned." % (retries, len(unassigned))

hoodIndex = Rtree()

print >>sys.stderr, "Buffering polygons."
for place_id, polygon in polygons.items():
    if type(polygon) is Polygon:
        polygon = Polygon(polygon.exterior.coords)
    else:
        bits = []
        for p in polygon.geoms:
            if type(p) is Polygon:
                bits.append(Polygon(p.exterior.coords))
        polygon = MultiPolygon(bits)
    polygons[place_id] = polygon.buffer(0)
    hoodIndex.insert(place_id, polygons[place_id].bounds)

print >>sys.stderr, "Retconning blocks to shapes."
cur.execute("""select geom, geoid10 FROM tabblock10 tb WHERE statefp10 = %s AND countyfp10 = %s AND blockce10 NOT LIKE '0%%'""", (statefp10, countyfp10))
for r in cur.fetchall():
  poly = wkb.loads(r[0].decode('hex'))
  id = r[1]
  candidates = [i for i in hoodIndex.intersection(poly.bounds)]
  found = False
  for place_id in candidates:
    hood = polygons[place_id]
    if hood.contains(poly):
      cur.execute("""DELETE FROM votes WHERE source=%s AND id=%s""", ('blockr', id))
      cur.execute("""INSERT INTO votes (id, label, count, source) values (%s, %s, %s, 'blockr')""", (
          id, place_id, 1))
      conn.commit()

      # print 'block %s in hood %s' % (id, place_id)
      found = True
      break

  if not found:
    print 'could not find a hood for block %s with %d candidates' % (id, len(candidates))

sys.exit(1)
 

print >>sys.stderr, "Writing output."
features = []
for place_id, poly in polygons.items():
    features.append({
        "type": "Feature",
        "id": place_id,
        "geometry": poly.__geo_interface__,
        "properties": {"woe_id": place_id, "name": names.get(place_id, "")}
    })

collection = {
    "type": "FeatureCollection",
    "features": features
}

print json.dumps(collection)

