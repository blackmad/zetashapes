#!/usr/bin/python

from shapely.geometry import Point, Polygon, MultiPolygon, asShape, LineString
from shapely.ops import cascaded_union, polygonize
import sys, json, math, pickle, os, geojson
import fiona
import json
import geojson
import traceback

do_polygonize = True
source = fiona.open(sys.argv[1], 'r')
lines = []
for index, feature in enumerate(source):
    if index % 1000 == 0:
      print "processed %s of %s" % (index, len(source))
    if feature['geometry']['type'] == 'LineString':
      coords = feature['geometry']['coordinates']
      for (start, end) in zip(coords[:-1], coords[1:]):
        lines.append(LineString([start, end]))
    if feature['geometry']['type'] == 'MultiLineString':
      for coords in feature['geometry']['coordinates']:
        for (start, end) in zip(coords[:-1], coords[1:]):
          lines.append(LineString([start, end]))

print >>sys.stderr, "%d lines read." % len(source)

outputFile = open(sys.argv[1] + '.json', 'w')
outputFile.write('{ "type": "FeatureCollection",   "features": [')
for index, poly in enumerate(polygonize(lines)):
  if index % 1000 == 0:
    print "wrote %s blocks so far" % (index)

  try:
    jsonGeom = json.loads(geojson.dumps(poly.__geo_interface__))

    if index != 0:
      outputFile.write(',')
    outputFile.write(json.dumps({'geometry': jsonGeom, 'properties': {}}))
  except:
    print b
    print traceback.print_exc()
outputFile.write(']}')
outputFile.close()

