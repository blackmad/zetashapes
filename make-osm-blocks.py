#!/usr/bin/python

from shapely.geometry import Point, Polygon, MultiPolygon, asShape, LineString
from shapely.ops import cascaded_union, polygonize, transform
import sys, json, math, pickle, os, geojson
from shapely.validation import explain_validity
from functools import partial
import fiona
import json
import geojson
import traceback
import pyproj

import rtree

from optparse import OptionParser
parser = OptionParser()
parser.add_option("--reload", dest="reload",  action="store_true", default=False)
parser.add_option("-r", "--resegment", dest="resegment",  action="store_true", default=False)
(options, args) = parser.parse_args()

rtree_basename = 'rtree'
should_do_load = True
if os.path.exists(rtree_basename + '.idx') and not options.reload:
  print 'found existing index %s.idx, and --reload not specified, reusing index' % rtree_basename
  should_do_load = False

idx = rtree.index.Index(rtree_basename, overwrite = should_do_load)
lineIndex = 0
lines = {}
minlat = sys.float_info.max
minlng = sys.float_info.max
maxlat = sys.float_info.min
maxlng = sys.float_info.min
def process_line(line):
  global lineIndex, minlat, minlng, maxlat, maxlng
  lineIndex += 1
  lines[lineIndex] = line
  for c in line.coords:
    minlat = min(minlat, c[1])
    maxlat = max(maxlat, c[1])
    minlng = min(minlng, c[0])
    maxlng = max(maxlng, c[0])

def loadGenerator():
  for f in args:
    source = fiona.open(f, 'r')
    for index, feature in enumerate(source):
      if index % 1000 == 0:
        print "loaded %s of %s" % (index, len(source))
      if feature['geometry']['type'] == 'LineString':
        coords = feature['geometry']['coordinates']
        for (start, end) in zip(coords[:-1], coords[1:]):
          line = LineString([start, end])
          process_line(line)
          yield (lineIndex, line.bounds, line)

      if feature['geometry']['type'] == 'MultiLineString':
        print 'got multilinestring'
        for coords in feature['geometry']['coordinates']:
          print coords
          for (start, end) in zip(coords[:-1], coords[1:]):
            line = LineString([start, end])
            process_line(line)
            yield (lineIndex, line.bounds, line)

# load everything into an rtree
def doLoad():
  global idx
  idx = rtree.index.Index(loadGenerator())

# for every line, fine all the intersections
def doResegment():
  global lines
  newLines = []
  for lineIndex, line in enumerate(lines.values()):
    if lineIndex % 1000 == 0:
      print "processed %s of %s" % (lineIndex, len(lines))

    lineParts = [line]
    # split the line into all the intersecting pieces
    intersections = idx.intersection(line.bounds, objects = True)
    for intersectingLine in intersections:
      newLineParts = []
      for linePart in lineParts:
        intersection = linePart.intersection(intersectingLine.object)
        if intersection.is_empty or intersection.coords[0] in linePart.coords:
          newLineParts.append(linePart)
        else:
          newLineParts.append(LineString([linePart.coords[0], intersection.coords[0]]))
          newLineParts.append(LineString([linePart.coords[1], intersection.coords[0]]))
      lineParts = newLineParts 
    newLines = newLines + lineParts

  lines = newLines

def writeBlocks(blocks, filename):
  outputFile = open(filename, 'w')
  outputFile.write('{ "type": "FeatureCollection",   "features": [')

  for index, poly in enumerate(blocks):
    if index % 1000 == 0:
      print "wrote %s blocks so far" % (index)

    try:
      if not poly.is_valid:
        poly = poly.buffer(0)

      jsonGeom = json.loads(geojson.dumps(poly.__geo_interface__))

      if index != 0:
        outputFile.write(',')
      outputFile.write(json.dumps({'geometry': jsonGeom, 'properties': {}}))
    except:
      print b
      print traceback.print_exc()
  outputFile.write(']}')
  outputFile.close()

def doPolygonize():
  blocks = polygonize(lines)
  writeBlocks(blocks, args[0] + '-blocks.geojson')

  blocks = polygonize(lines)
  bounds = Polygon([
    [minlng, minlat],
    [minlng, maxlat],
    [maxlng, maxlat],
    [maxlng, minlat],
    [minlng, minlat]
  ])
  # Geometry transform function based on pyproj.transform
  project = partial(
    pyproj.transform,
    pyproj.Proj(init='EPSG:3785'),
    pyproj.Proj(init='EPSG:4326'))
  print bounds
  print transform(project, bounds)

  print 'finding holes'
  for index, block in enumerate(blocks):
    if index % 1000 == 0:
      print "diff'd  %s" % (index)
    if not block.is_valid:
      print explain_validity(block)
      print transform(project, block)
    else:
      bounds = bounds.difference(block)
  print bounds

if should_do_load:
  doLoad()
if options.resegment:
  doResegment()
else:
  lines = lines.values()
doPolygonize()

