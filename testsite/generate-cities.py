#!/usr/bin/python

import json
import re
from functools import wraps
from collections import namedtuple
import psycopg2
import psycopg2.extras
from collections import defaultdict
import os
from itertools import groupby
from shapely.ops import cascaded_union
from shapely.geometry import mapping, asShape
from shapely import speedups
import app.geo_utils

conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cur.execute("select * FROM geoname WHERE population > 0 AND country = 'US'")
places = []
for r in cur:
  if r['admin2'] and r['fclass'] == 'P':
    areaid = '%s%s' % (app.geo_utils.state_codes[r['admin1']], r['admin2'])
    name = r['name'].replace('City of', '').replace('Town of', '').replace('Village of', '').strip()
    places.append(("[\"%s, %s\",%s]," % (name, r['admin1'], areaid), r['population']))

for r in sorted(list(set(places)), key=lambda x: x[1]*-1):
  print r[0]

