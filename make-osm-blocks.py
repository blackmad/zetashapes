#!/usr/bin/python

from shapely.geometry import Point, Polygon, MultiPolygon, asShape
from shapely.ops import cascaded_union, polygonize
import sys, json, math, pickle, os, geojson
import fiona
import geojson
import traceback

do_polygonize = True
source = fiona.open(sys.argv[1], 'r')
lines = []
for index, feature in enumerate(source):
    if index % 1000 == 0:
      print "processed %s of %s" % (index, len(source))
    if feature['geometry']['type'] in ('LineString', 'MultiLineString'):
      # should we check on these?
      # EdgeRing::getRingInternal: IllegalArgumentException: Invalid number of points in LinearRing found 3 - must be 0 or >= 4
      lines.append(asShape(feature['geometry']))
print >>sys.stderr, "%d lines read." % len(source)
blocks = [poly.__geo_interface__ for poly in  polygonize(lines)]
features = []
for b in blocks:
  try:
    jsonGeom = geojson.dumps(b)
    features.append(
      geojson.Feature(geometry=jsonGeom, properties={})
    )
  except:
    print b
    print traceback.print_exc()
fc = geojson.FeatureCollection(features)
geojson.dumps(fc, sys.argv[1] + '.json')

