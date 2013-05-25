#!/usr/bin/python

import sys
import psycopg2
import json

conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
cur = conn.cursor()

areaid = sys.argv[1]
statefp10 = areaid[0:2]
countyfp10 = areaid[2:]

def makeFeature(row):
  return {
    "type": "Feature",
    "geometry": eval(row[1]),
    "properties": {
      "id": row[0]
    }
  } 

output = open('static/json/%s.json' % areaid, 'w')
cur.execute("""select geoid10, ST_AsGeoJSON(ST_Transform(geom, 4326)) as geojson_geom FROM tabblock10 tb WHERE statefp10 = %s AND countyfp10 = %s AND blockce10 NOT LIKE '0%%'""", (statefp10, countyfp10))
blocks = []
for r in cur:
  blocks.append(makeFeature(r))

response = {
  "type": "FeatureCollection",
  "features": blocks
}
json.dump(response, output)


