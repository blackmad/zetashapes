#!/usr/bin/python

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
import vote_utils
from rtree import Rtree
from shapely.geometry import asShape
import geojson

index = Rtree('/tmp/smoothr.rt')

conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
cur = conn.cursor()

def processArea(areaid):
  (rows, voteDict) = vote_utils.getVotes(conn, areaid, None)
  bestVoteDict = {}
  print 'building vote dict'
  for k,v in voteDict.iteritems():
    bestVoteDict[str(k).zfill(15)] = vote_utils.pickBestVote(v) 

  print 'building rtree'
  shapeDict = {}
  for r in rows:
    id = r['geoid10']
    shape = asShape(geojson.loads(r['geojson_geom']))
    shapeDict[id] = shape
    index.add(int(id), shape.bounds)

  print 'smoothin'

  for r in rows:
    id = str(r['geoid10']).zfill(15)
    bestId = None
    if id in bestVoteDict:
      bestId = bestVoteDict[id]['id']
    shape = shapeDict[id]
    # find all the blocks it maybe touches
    candidate_ids = set([n for n in index.intersection(shapeDict[id].bounds)])
    touches = []
    for cid in candidate_ids:
      if cid != id:
        cshape = shapeDict[str(cid).zfill(15)]
        if shape.touches(cshape):
          touches.append(cid)
    print '%s touches %s' % (id, touches)
    smearDict = defaultdict(lambda: 0)
    totalWithVotes = 0
    for t in touches:
      tid = str(t).zfill(15)
      if tid in bestVoteDict:
        cbestId = bestVoteDict[tid]['id']
        smearDict[cbestId] += 1
        totalWithVotes += 1
    print smearDict
    if len(smearDict) > 0:
      maxVote = max(smearDict.iteritems(), key=operator.itemgetter(1))
      threshold = totalWithVotes * (5.0/8.0)
      if maxVote[1] >= threshold and maxVote[0] != bestId:
        print 'very likely that block %s should be in %s, is in %s' % (id, maxVote[0], bestId)
        cur.execute("""DELETE FROM votes WHERE source=%s AND id=%s""", ('smear', id))
        cur.execute("""INSERT INTO votes (id, label, count, source) values (%s, %s, %s, 'smear')""", (
            id, maxVote[0], 1))
        conn.commit()

import sys
for s in sys.argv[1:]:
  processArea(s)
