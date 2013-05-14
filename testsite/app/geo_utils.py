#!/usr/bin/python

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
import os
import json
from itertools import groupby
from shapely.ops import cascaded_union
from shapely.geometry import mapping, asShape
from shapely import speedups

state_codes = {
    'WA': '53', 'DE': '10', 'DC': '11', 'WI': '55', 'WV': '54', 'HI': '15',
    'FL': '12', 'WY': '56', 'PR': '72', 'NJ': '34', 'NM': '35', 'TX': '48',
    'LA': '22', 'NC': '37', 'ND': '38', 'NE': '31', 'TN': '47', 'NY': '36',
    'PA': '42', 'AK': '02', 'NV': '32', 'NH': '33', 'VA': '51', 'CO': '08',
    'CA': '06', 'AL': '01', 'AR': '05', 'VT': '50', 'IL': '17', 'GA': '13',
    'IN': '18', 'IA': '19', 'MA': '25', 'AZ': '04', 'ID': '16', 'CT': '09',
    'ME': '23', 'MD': '24', 'OK': '40', 'OH': '39', 'UT': '49', 'MO': '29',
    'MN': '27', 'MI': '26', 'RI': '44', 'KS': '20', 'MT': '30', 'MS': '28',
    'SC': '45', 'KY': '21', 'OR': '41', 'SD': '46'
}

fips_codes = {v:k for k, v in state_codes.iteritems()}

def areaInfo(rows):
  responses = []
  for r in rows:
    responses.append({
      'displayName': "%s, %s" % (r['name10'], fips_codes[r['statefp10']]),
      'name': r['name10'],
      'state': fips_codes[r['statefp10']],
      'areaid': r['geoid10'],
      'lat': r['intptlat10'],
      'lng': r['intptlon10'],
      'bbox': json.loads(r['bbox'])
    })
  return responses

def getNearestCounties(conn, lat, lng):
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  cur.execute("""select * FROM tl_2010_us_county10 WHERE ST_DWithin(ST_SetSRID(ST_MakePoint(%s, %s), 4326), geom, 0.1)""", (lng, lat))
  rows = cur.fetchall()
  return areaInfo(rows)

def getInfoForAreaIds(conn, areaids):
  cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
  cur.execute("""select *,ST_AsGeoJson(ST_Envelope(geom)) as bbox  FROM tl_2010_us_county10 WHERE geoid10 IN %s""", (tuple(areaids),))
  rows = cur.fetchall()
  return areaInfo(rows)
