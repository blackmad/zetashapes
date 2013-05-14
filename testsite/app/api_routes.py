#!/usr/bin/python

# TODO
# return 'me' votes section in blockdata call

from flask import Flask
import flask_gzip
import json
import re
from functools import wraps
from collections import namedtuple
from flask import redirect, request, current_app, jsonify
import psycopg2
import psycopg2.extras
from collections import defaultdict
from . import app, db
import os
from itertools import groupby
from shapely.ops import cascaded_union
from shapely.geometry import mapping, asShape
from shapely import speedups

if speedups.available:
  print 'shapely speedups available!!!!'
  speedups.enable()

# start using sqlalchemy cursor
conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")

def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args,**kwargs).data) + ')'
            return current_app.response_class(content, mimetype='application/javascript')
        else:
            return f(*args, **kwargs)
    return decorated_function


def makeFeature(row, voteDict, user):
  return {
    "type": "Feature",
    "geometry": eval(row['geojson_geom']),
    "properties": {
      "id": row['geoid10'],
      "votes": [x for x in [pickBestVote(voteDict[row['geoid10']])] if x]
    }
  }

def makeFeatures(rows, voteDict, user):
  return [makeFeature(r, voteDict, user) for r in rows]

@app.route('/api/stateCounts', methods=['GET'])
@support_jsonp
def stateCounts():
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  cur.execute("""select areaid, count, name10  FROM area_counts JOIN tl_2010_us_state10 ON areaid = geoid10 where char_length(areaid) = 2""")
  rows = cur.fetchall()
  ret = {}
  for r in rows:
    ret[r['areaid']] = {
      'name': r['name10'],
      'count': r['count']
    }
  return jsonify(ret)

@app.route('/api/blocksByGeom', methods=['GET'])
@support_jsonp
def blocksByArea():
  cur = conn.cursor()

  ll = request.args.get('ll', False)
  if len(ll.split(',')) < 4:
    wkt = 'LINESTRING(%s)' % ll
  else: 
    wkt = 'POLYGON((%s))' % ll
  print wkt

  comm = cur.mogrify("""select geoid10 FROM tabblock10 tb WHERE ST_Intersects(geom, ST_Transform(ST_GeomFromText(%s, 4326), 4326)) AND blockce10 NOT LIKE '0%%'""", (wkt,))
  print(comm)
  cur.execute(comm)
  rows = cur.fetchall()
  return jsonify({'ids': [r[0] for r in rows]})

def getVotes(areaid, user): 
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

  statefp10 = areaid[0:2]
  countyfp10 = areaid[2:]

  cur.execute("""select geoid10, ST_AsGeoJSON(ST_Transform(geom, 4326)) as geojson_geom FROM tabblock10 tb WHERE statefp10 = %s AND countyfp10 = %s AND blockce10 NOT LIKE '0%%'""", (statefp10, countyfp10))
  rows = cur.fetchall()

  cur.execute("""select woe_id, id, label, count, source, name FROM votes v JOIN geoplanet_places ON label::int = woe_id WHERE id LIKE '%s%%'""" % (areaid))

  votes = defaultdict(list)
  for r in cur.fetchall():
    votes[r['id']].append({
      'label': r['name'], 
      'id': r['woe_id'], 
      'count': r['count'], 
      'source': r['source']
    })
 
  user_votes = {}
  print 'user? %s' % user
  print user
  if user:
    userId = user['id']
    cur.execute("""select g.woe_id, blockid, name, weight FROM user_votes v JOIN geoplanet_places g ON v.woe_id = g.woe_id WHERE v.userid = %s AND v.blockid LIKE '%s%%'""" % (userId, areaid))
    for r in cur.fetchall():
      votes[r['blockid']].append({
        'label': r['name'], 
        'id': r['woe_id'], 
        'source': 'self',
        'count': r['weight']
      })

  return (rows, votes)

@app.route('/api/blocksByArea', methods=['GET'])
@support_jsonp
def citydata():
  areaid = request.args.get('areaid', False)
  apikey = request.args.get('key', '')

  user = findUserByApiKey(apikey)
  (rows, votes) = getVotes(areaid, user)

  response = {
    "type": "FeatureCollection",
    "features": makeFeatures(rows, votes, user)
  }

  return jsonify(response)

def pickBestVote(votes):
  maxVote = None
  selfVote = [v for v in votes if v['source'] == 'self']
  if len(selfVote) > 0:
    selfVote = selfVote[0]
    if selfVote['count'] == -1:
      votes = [v for v in votes if v['id'] != selfVote['id']]
    else:
      maxVote = selfVote
  if not maxVote and len(votes) > 0:
    maxVote = max(votes, key=lambda x:x['count'])
  return maxVote


def getNeighborhoodsByArea(areaid, user):
  (blocks, allVotes) = getVotes(areaid, user)

  blocks_by_hoodid = defaultdict(list)
  id_to_label = {}

  for block in blocks:
    geom = asShape(eval(block['geojson_geom']))
    votes = allVotes[block['geoid10']]
    maxVote = pickBestVote(votes)
    if maxVote:
      blocks_by_hoodid[maxVote['id']].append(geom)
      id_to_label[maxVote['id']] = maxVote['label']

  neighborhoods = []
  for (id, geoms) in blocks_by_hoodid.iteritems():
    merged = cascaded_union(geoms)
    geojson = { 
      'type': 'Feature',
      'properties': {
        'id': id,
        'label': id_to_label[id]
      },
      'geometry': mapping(merged)
    }
    neighborhoods.append(geojson)
  
  response = {
    "type": "FeatureCollection",
    "features": neighborhoods
  }

  return jsonify(response)

@app.route('/api/neighborhoodsByArea', methods=['GET'])
@support_jsonp
def neighborhoodsByArea():
  areaid = request.args.get('areaid', False)
  apikey = request.args.get('key', '')
  user = findUserByApiKey(apikey)
  return getNeighborhoodsByArea(areaid, user)


@app.route('/api/labels', methods=['GET'])
@support_jsonp
def labels():
  cur = conn.cursor()

  areaid = request.args.get('areaid', False)

  statefp10 = areaid[0:2]
  countyfp10 = areaid[2:]

  cur.execute("""select distinct(label, name) FROM votes v JOIN geoplanet_places ON label::int = woe_id WHERE id LIKE '%s%%'""" % (areaid))

  rows = cur.fetchall()

  response = []
  for r in rows:
    p = re.compile("\\((\d+),(.*)\\)")
    m = p.match(r[0])
    if m:
      id = m.group(1)
      label = m.group(2).replace('"', '')
      response.append({'id': id, 'label': label})
      
  return jsonify({'labels': response})

# this should probably go through the user model? meh
def findUserByApiKey(api_key):
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  cur.execute("""select * FROM users WHERE api_key=%s""",  (api_key,))
  return cur.fetchone()

def modifyUsersVoteCount(cur, userLevel, blockid, woeid, incr):
  cur.execute("""update votes SET count = count + %s WHERE label=%s AND id=%s""", (
    incr, woeid, blockid
  ))

IncomingBlockVote = namedtuple('IncomingBlockVote', ['blockid', 'woe_id', 'weight'], verbose=True)

# get is only for testing
@app.route('/api/vote', methods=['POST', 'GET'])
@support_jsonp
def do_vote():
  with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
    votepairs = []
    
    blockid = request.args.get('blockid', '')
    label = request.args.get('label', '')
    if blockid and label:
      blockids = blockid.split(',')
      for id in blockids:
        votepairs.append(IncomingBlockVote(id, label, 1))
    else:
      votes = request.args.get('votes', '')

      # votes are in the form blockid,woeid;blockid,woeid;...
      for votepair in votes.split(';'):
        print votepair
        print votepair.split(',')
        voteparts = votepair.split(',')

        if len(voteparts) == 2:
          votepairs.append(IncomingBlockVote(voteparts[0], int(voteparts[1]), 1))
        elif len(voteparts) == 3:
          votepairs.append(IncomingBlockVote(voteparts[0], int(voteparts[1]), int(voteparts[2])))
    
    print votepairs

    apikey = request.args.get('key', '')
    user = findUserByApiKey(apikey)
    userId = user['id']

    if len(votepairs) == 0:
      return jsonify({})

    comm = cur.mogrify("""select * FROM user_votes WHERE userid=%s AND blockid IN %s""", (
      userId,
      tuple([v[0] for v in votepairs])
    ))
    print comm
    cur.execute(comm)

    rows = cur.fetchall()
    print rows
    existing_votes = defaultdict(list)
    for v in rows:
      existing_votes[v['blockid']].append(v)
    print existing_votes

    for vote in votepairs:
      print 'looking at label vote %s for block %s' % (vote.woe_id, vote.blockid)
      print existing_votes[vote.blockid]

      already_had_vote = False
      for existing_vote in existing_votes[vote.blockid]:
        print 'existing vote %s' % existing_vote
        if existing_vote['woe_id'] == vote.woe_id and existing_vote['weight'] == vote.weight:
          already_had_vote = True
          print 'matched'
        else:
          print 'didnot match'
          modifyUsersVoteCount(cur, vote.blockid, existing_vote['woe_id'], -1*vote['weight'])
          print cur.mogrify("""DELETE FROM user_votes WHERE userid=%s AND blockid=%s AND woe_id=%s""", (
            userId, vote.blockid, existing_vote['woe_id']))

          cur.execute("""DELETE FROM user_votes WHERE userid=%s AND blockid=%s AND woe_id=%s""", (
            userId, vote.blockid, existing_vote['woe_id']))

      if not already_had_vote:
        cur.execute("""select COUNT(*) as c FROM votes WHERE source='users' AND id=%s AND label=%s""", (
          vote.blockid, vote.woe_id
        ))
        if cur.fetchone()['c'] > 0:
          # we have an existing row to increment
          modifyUsersVoteCount(cur, user['level'], vote.blockid, vote.woe_id, vote.weight)
        else:
          print 'trying to insert'
          cur.execute("""INSERT INTO votes (id, label, count, source) values (%s, %s, %s, 'users')""", (
            vote.blockid, vote.woe_id, vote.weight))
      
        cur.execute("""INSERT INTO user_votes (userid, blockid, woe_id, weight, ts) values (%s, %s, %s, %s, 'now')""", (
          userId, vote.blockid, vote.woe_id, vote.weight))
        conn.commit()
          
      # see if I have an existing vote on user_votes for this block
      # if I do, and it's for the same woe_id, don't do anything
      # if it's for a different block
      # --ugh, see if there's an existing user votes row for new block, if there is, increment it, if not, create it
      # existing user votes row should exist, so just decrement it
    return getNeighborhoodsByArea(votepairs[0].blockid[0:5], user)
