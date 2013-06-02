#!/usr/bin/python

# TODO
# return 'me' votes section in blockdata call

from flask import Flask
import flask_gzip
import json
import re
from functools import wraps
from collections import namedtuple
from flask import redirect, request, current_app
import psycopg2
import psycopg2.extras
from collections import defaultdict
from . import app, db
import os
from itertools import groupby
from shapely.ops import cascaded_union
from shapely.geometry import mapping, asShape
from shapely import speedups
import geo_utils
import vote_utils
import sqlalchemy.pool as pool

def jsonify(*args, **kwargs):
  return current_app.response_class(json.dumps(dict(*args, **kwargs), indent=None), mimetype='application/json')

if speedups.available:
  print 'shapely speedups available!!!!'
  speedups.enable()

# start using sqlalchemy cursor, models etc, please
psycopg2 = pool.manage(psycopg2)


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
      "votes": [x for x in [vote_utils.pickBestVote(voteDict[row['geoid10']])] if x]
    }
  }

def makeFeatures(rows, voteDict, user):
  return [makeFeature(r, voteDict, user) for r in rows]

@app.route('/api/stateCounts', methods=['GET'])
@support_jsonp
def stateCounts():
  conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
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
  conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
  cur = conn.cursor()

  ll = request.args.get('ll', False)
  if len(ll.split(',')) < 4:
    wkt = 'LINESTRING(%s)' % ll
  else: 
    wkt = 'POLYGON((%s))' % ll

  comm = cur.mogrify("""select geoid10 FROM tabblock10 tb WHERE ST_Intersects(geom, ST_Transform(ST_GeomFromText(%s, 4326), 4326)) AND blockce10 NOT LIKE '0%%'""", (wkt,))
  cur.execute(comm)
  rows = cur.fetchall()
  return jsonify({'ids': [r[0] for r in rows]})

@app.route('/api/blocksByArea', methods=['GET'])
@support_jsonp
def citydata():
  conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
  areaid = request.args.get('areaid', False)
  apikey = request.args.get('key', '')

  user = findUserByApiKey(apikey)
  (rows, votes) = vote_utils.getVotes(conn, areaid, user)

  response = {
    "type": "FeatureCollection",
    "features": makeFeatures(rows, votes, user)
  }

  return jsonify(response)

def getNeighborhoodsByArea(areaid, user):
  conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
  neighborhoods = geo_utils.getNeighborhoodsGeoJsonByArea(conn, areaid, user)
  
  response = {
    "type": "FeatureCollection",
    "features": neighborhoods
  }

  jresponse = jsonify(response)
  
  intent = request.args.get('intent', None)
  if intent == 'download':
    jresponse.headers['Content-Disposition'] = 'attachment; filename=%s.json' % areaid
  print jresponse

  return jresponse

@app.route('/api/neighborhoodsByArea', methods=['GET'])
@support_jsonp
def neighborhoodsByArea():
  conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
  areaid = request.args.get('areaid', False)
  apikey = request.args.get('key', '')
  user = findUserByApiKey(apikey)
  return getNeighborhoodsByArea(areaid, user)

@app.route('/api/areaInfo')
@support_jsonp
def areaInfo():
  conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
  areaid = request.args.get('areaid', '').split(',')
  areaInfos = geo_utils.getInfoForAreaIds(conn, areaid)
  return jsonify({'areas': areaInfos})

@app.route('/api/blockInfo')
@support_jsonp
def blockInfo():
  apikey = request.args.get('key', '')
  user = findUserByApiKey(apikey)
  conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
  blockids = request.args.get('blockid', '').split(',')
  voteDict = vote_utils.getVotesForBlocks(conn, blockids, user)

  responseDict = {}
  for (blockid, votes) in voteDict.iteritems():
    responseDict[blockid] = {
      'votes': votes,
      'bestVote': vote_utils.pickBestVote(votes)
    }
  
  return jsonify(responseDict)

@app.route('/api/labels', methods=['GET'])
@support_jsonp
def labels():
  conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
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
  if (api_key):
    conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""select * FROM users WHERE api_key=%s""",  (api_key,))
    return cur.fetchone()
  else:
    return None

def modifyUsersVoteCount(cur, userLevel, blockid, woeid, incr):
  conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")

  cur.execute("""update votes SET count = count + %s WHERE label=%s AND id=%s""", (
    incr, woeid, blockid
  ))

IncomingBlockVote = namedtuple('IncomingBlockVote', ['blockid', 'woe_id', 'weight'])

# get is only for testing
@app.route('/api/vote', methods=['POST', 'GET'])
@support_jsonp
def do_vote():
  conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  votepairs = []
  formdata = request.form or request.args
  
  blockid = formdata.get('blockid', '')
  label = formdata.get('label', '')
  if blockid and label:
    blockids = blockid.split(',')
    for id in blockids:
      votepairs.append(IncomingBlockVote(id, label, 1))
  else:
    votes = formdata.get('votes', '')

    # votes are in the form blockid,woeid;blockid,woeid;...
    for votepair in votes.split(';'):
      #print votepair
      #print votepair.split(',')
      voteparts = votepair.split(',')

      if len(voteparts) == 2:
        votepairs.append(IncomingBlockVote(voteparts[0], int(voteparts[1]), 1))
      elif len(voteparts) == 3:
        votepairs.append(IncomingBlockVote(voteparts[0], int(voteparts[1]), int(voteparts[2])))
  
  #print votepairs

  apikey = formdata.get('key', '')
  user = findUserByApiKey(apikey)
  userId = user['id']

  if len(votepairs) == 0:
    return jsonify({})

  comm = cur.mogrify("""select * FROM user_votes WHERE userid=%s AND blockid IN %s""", (
    userId,
    tuple([v[0] for v in votepairs])
  ))
  #print comm
  cur.execute(comm)

  rows = cur.fetchall()
  #print rows
  existing_votes = defaultdict(list)
  for v in rows:
    existing_votes[v['blockid']].append(v)
  #print existing_votes

  for vote in votepairs:
    #print 'looking at label vote %s for block %s' % (vote.woe_id, vote.blockid)
    #print existing_votes[vote.blockid]

    already_had_vote = False
    for existing_vote in existing_votes[vote.blockid]:
      #print 'existing vote %s' % existing_vote
      if existing_vote['woe_id'] == vote.woe_id and existing_vote['weight'] == vote.weight:
        already_had_vote = True
        #print 'matched'
      else:
        #print 'didnot match'
        #print existing_vote
        #print vote
        #print existing_vote['woe_id']
        #print vote.weight
        modifyUsersVoteCount(cur, user['level'], vote.blockid, existing_vote['woe_id'], -1*vote.weight)

    if not already_had_vote:
      cur.execute("""select COUNT(*) as c FROM votes WHERE source='users' AND id=%s AND label=%s""", (
        vote.blockid, vote.woe_id
      ))
      if cur.fetchone()['c'] > 0:
        # we have an existing row to increment
        modifyUsersVoteCount(cur, user['level'], vote.blockid, vote.woe_id, vote.weight)
      else:
        #print 'trying to insert'
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
