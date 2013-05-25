#!/usr/bin/python

import fiona
from shapely.geometry import asShape
from shapely.geometry import mapping
import psycopg2
import sys
import itertools

def levenshtein(a,b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n
        
    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
            
    return current[n]

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")

conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")
cur = conn.cursor()

def find_place(name, placetype, parent=None):
  print 'looking for %s of %s in %s' % (name, placetype, parent)
  cur.execute("select woe_id, parent_id FROM geoplanet_places WHERE name = %s AND placetype = %s", (name, placetype))
  rows = cur.fetchall()
  print rows
  if parent:
    rows = [r for r in rows if r[1] == parent]
  if len(rows) > 1:
    print 'ambiguous!!!'
    print rows
    sys.exit(1)
  if len(rows) == 0:
    print "could not find at all"
    sys.exit(1)
  return rows[0][0]

def find_children(ids):
  if len(ids) == 0:
    return []
  cur.execute("select woe_id FROM geoplanet_places WHERE parent_id IN %s", (tuple(ids),))
  rows = list([i[0] for i in cur.fetchall()])
  return rows + find_children(rows)

filename = sys.argv[1]
placeparts = sys.argv[2].split(',')
colname = sys.argv[3]
sourcename = sys.argv[4]

parentid = None
for i in range(0, len(placeparts), 2):
  placename = placeparts[i]
  placetype = placeparts[i+1]
  parentid = find_place(placename, placetype, parentid)

def normalize(s):
  return s.lower().replace(' ', '').replace('-', '')

def add_place(name):
  cur.execute("insert into geoplanet_places values ((select max(woe_id) FROM geoplanet_places) +1, 'US', %s, 'en', 'Suburb', %s) RETURNING woe_id", (name, parentid))
  conn.commit()
  return cur.fetchone()[0]

validids = find_children([parentid,])
cur.execute("select name, woe_id FROM geoplanet_places WHERE woe_id IN %s AND placetype='Suburb'", (tuple(validids),))
placeDict = {}
placeNameDict = {}
for r in cur.fetchall():
  name = normalize(r[0])
  placeDict[name] = r[1]
  placeNameDict[name] = r[0]

bestLabels = {}

for f in fiona.open(filename, 'r'):
  hoodname = normalize(f['properties'][colname])
  if hoodname not in placeDict:
    print f['properties'][colname]
    print hoodname
    for n in placeDict.keys():
      if levenshtein(n, hoodname) < 5:
        if query_yes_no('Accept match %s %s?' % (n, hoodname), 'no'):
          hoodid = placeDict[n]
        else:
          hoodid = add_place(f['properties'][colname])
      else:
        hoodid = add_place(f['properties'][colname])
  else:
    hoodid = placeDict[hoodname]

  wkt = asShape(f['geometry']).wkt
  cur.execute("""select geoid10, ST_Area(ST_Intersection(geom, ST_GeomFromText(%s, 4326))) / ST_Area(ST_GeomFromText(%s, 4326)) FROM tabblock10 tb WHERE ST_Intersects(geom, ST_Transform(ST_GeomFromText(%s, 4326), 4326)) AND blockce10 NOT LIKE '0%%'""", (wkt,wkt, wkt))
  for r in cur.fetchall():
    geoid = r[0]
    overlap = r[1]
    if id not in bestLabels:
      bestLabels[geoid] = (hoodid, overlap)
    elif bestLabels[geoid] < overlap:
      print 'superceding %s for %s with %s' % (bestLabels[geoid], geoid, hoodid)
      bestLabels[geoid] = (hoodid, overlap)

source = 'official-%s' % sourcename
cur.execute("""DELETE FROM votes WHERE source = %s""", (source,))

for (geoid, hoodid) in bestLabels.items():
  cur.execute("""INSERT INTO votes (id, label, count, source) values (%s, %s, %s, %s)""", (
    geoid, hoodid[0], 1, source))
conn.commit()
