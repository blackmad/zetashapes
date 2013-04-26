#!/usr/bin/python
from flask import Flask
import flask_gzip
import json
import re
from functools import wraps
from flask import redirect, request, current_app, jsonify
import psycopg2
import psycopg2.extras
from collections import defaultdict

conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")

app = Flask(__name__)

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

@app.route('/blocksByGeom', methods=['GET'])
@support_jsonp
def blocksByArea():
  cur = conn.cursor()

  ll = request.args.get('ll', False)
  if len(ll.split(',')) < 4:
    wkt = 'LINESTRING(%s)' % ll
  else: 
    wkt = 'POLYGON((%s))' % ll
  print wkt

  comm = cur.mogrify("""select geoid10 FROM tabblock10 tb WHERE ST_Intersects(geom, ST_Transform(ST_GeomFromText(%s, 4326), 4326))""", (wkt,))
  print(comm)
  cur.execute(comm)
  rows = cur.fetchall()
  return jsonify({'ids': [r[0] for r in rows]})


@app.route('/citydata', methods=['GET'])
@support_jsonp
def citydata():
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

  areaid = request.args.get('areaid', False)

  statefp10 = areaid[0:2]
  countyfp10 = areaid[2:]

  cur.execute("""select geoid10, ST_AsGeoJSON(ST_Transform(geom, 4326)) as geojson_geom FROM tabblock10 tb WHERE statefp10 = %s AND countyfp10 = %s""", (statefp10, countyfp10))
  rows = cur.fetchall()

  print cur.mogrify("""select id, label, count, source, name FROM votes v JOIN geoplanet_places ON label::int = woe_id WHERE id LIKE '%s%%'""" % (areaid))
  cur.execute("""select id, label, count, source, name FROM votes v JOIN geoplanet_places ON label::int = woe_id WHERE id LIKE '%s%%'""" % (areaid))
  votes = defaultdict(list)
  for r in cur.fetchall():
    votes[r['id']].append({
      'label': r['name'], 
      'id': r['id'], 
      'count': r['count'], 
      'source': r['source']
    })

  response = {
    "type": "FeatureCollection",
    "features": makeFeatures(rows, votes)
  }

  return jsonify(response)

@app.route('/labels', methods=['GET'])
@support_jsonp
def labels():
  cur = conn.cursor()

  areaid = request.args.get('areaid', False)

  statefp10 = areaid[0:2]
  countyfp10 = areaid[2:]

  cur.execute("""select distinct(label, name) FROM votes v JOIN geoplanet_places ON label::int = woe_id WHERE statefp10 = %s AND countyfp10 = %s""",(statefp10, countyfp10))
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


if __name__ == '__main__':
  flask_gzip.Gzip(app)
  app.run(debug=True, 
   host='0.0.0.0'
  )
