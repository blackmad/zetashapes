#!/usr/bin/python

# TODO
# return 'me' votes section in blockdata call

from flask import Flask
import flask_gzip
import json
import re
from functools import wraps
from flask import redirect, request, current_app, jsonify
import psycopg2
import psycopg2.extras
from collections import defaultdict
from . import app, db
import os
from itertools import groupby

TMP_DIR = '/tmp'

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


def makeFeature(row, voteDict):
  return {
    "type": "Feature",
    "geometry": eval(row['geojson_geom']),
    "properties": {
      "id": row['geoid10'],
      "votes": voteDict[row['geoid10']]
    }
  }

def makeFeatures(rows, voteDict):
  return [makeFeature(r, voteDict) for r in rows]

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


@app.route('/api/citydata', methods=['GET'])
@support_jsonp
def citydata():
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

  areaid = request.args.get('areaid', False)

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

  response = {
    "type": "FeatureCollection",
    "features": makeFeatures(rows, votes)
  }

  return jsonify(response)

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
    print r
    p = re.compile("\\((\d+),(.*)\\)")
    m = p.match(r[0])
    if m:
      id = m.group(1)
      label = m.group(2).replace('"', '')
      response.append({'id': id, 'label': label})
      
  print rows
  return jsonify({'labels': response})

# this should probably go through the user model? meh
def findUserByApiKey(api_key):
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  cur.execute("""select * FROM users WHERE api_key=%s""",  (api_key,))
  return cur.fetchone()

def modifyUsersVoteCount(cur, blockid, woeid, incr):
  cur.execute("""update votes SET count = count + %s WHERE label=%s AND id=%s""", (
    incr, woeid, blockid
  ))

# get is only for testing
@app.route('/api/vote', methods=['POST', 'GET'])
@support_jsonp
def do_vote():
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

  votes = request.args.get('votes', '')
  apikey = request.args.get('key', '')

  # votes are in the form blockid,woeid;blockid,woeid;...
  votepairs = []
  for votepair in votes.split(';'):
    print votepair
    print votepair.split(',')
    blockid = votepair.split(',')[0]
    woeid = int(votepair.split(',')[1])
    votepairs.append((blockid, woeid))

  user = findUserByApiKey(apikey)
  userId = user['id']

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

  for (blockid, woeid) in votepairs:
    print 'looking at label vote %s for block %s' % (woeid, blockid)
    print existing_votes[blockid]

    already_had_vote = False
    for existing_vote in existing_votes[blockid]:
      print 'existing vote %s' % existing_vote
      if existing_vote['woe_id'] == woeid:
        already_had_vote = True
        print 'matched'
      else:
        print 'didnot match'
        modifyUsersVoteCount(cur, blockid, existing_vote['woe_id'], -1)
        print cur.mogrify("""DELETE FROM user_votes WHERE userid=%s AND blockid=%s AND woe_id=%s""", (
          userId, blockid, existing_vote['woe_id']))

        cur.execute("""DELETE FROM user_votes WHERE userid=%s AND blockid=%s AND woe_id=%s""", (
          userId, blockid, existing_vote['woe_id']))

    if not already_had_vote:
      cur.execute("""select COUNT(*) as c FROM votes WHERE source='users' AND id=%s AND label=%s""", (
        blockid, int(woeid)
      ))
      if cur.fetchone()['c'] > 0:
        # we have an existing row to increment
        modifyUsersVoteCount(cur, blockid, int(woeid), 1)
      else:
        print 'trying to insert'
        cur.execute("""INSERT INTO votes (id, label, count, source) values (%s, %s, 1, 'users')""", (
          blockid, int(woeid)))
    
      cur.execute("""INSERT INTO user_votes (userid, blockid, woe_id) values (%s, %s, %s)""", (
        userId, blockid, int(woeid)))
      conn.commit()
        
    # see if I have an existing vote on user_votes for this block
    # if I do, and it's for the same woe_id, don't do anything
    # if it's for a different block
    # --ugh, see if there's an existing user votes row for new block, if there is, increment it, if not, create it
    # existing user votes row should exist, so just decrement it

#    cur = conn.cursor()
#    cur.execute("""UPDATE votes SET label=%s, count=%s, source=%s WHERE id=%s AND source='flickr' AND label=%s""", (
#      woeid, counts[blockid][woeid], blockid, woeid))
  # return jsonify({'labels': response})
