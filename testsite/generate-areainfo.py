#!/usr/bin/python

import json
import re
from functools import wraps
from collections import namedtuple
import psycopg2
import psycopg2.extras
from collections import defaultdict
import os
import sys
from itertools import groupby
from shapely.ops import cascaded_union
from shapely.geometry import mapping, asShape
from shapely import speedups
import app.geo_utils

conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")

areaid = sys.argv[1]

areaInfos = app.geo_utils.getInfoForAreaIds(conn, [areaid,])
json.dump({'areas': areaInfos}, open('app/static/json/info-%s.json' % areaid, 'w'))
