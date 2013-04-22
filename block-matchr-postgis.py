#!/usr/bin/python

import psycopg2
from collections import defaultdict

# SELECT * FROM "tabblock2010_36_pophu-900913" WHERE ST_CONTAINS(geom, ST_Transform(ST_GeomFromText('POINT(-74 40.74)', 4326), 900913));

import sys

ID_COL = 'geoid10'
TABLE = 'tabblock10'
FROM_SRID = 4326
TABLE_SRID = 4326
# TABLE_SRID = 900913

VOTE_TABLE = 'votes'

conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")

counts = defaultdict(lambda: defaultdict(int))

c = 0
input_file = open(sys.argv[1])
for line in input_file:
  line = line.strip()
  c += 1
  if (c % 1000) == 0:
    print 'finished %d input lines' % c
  #3502363673      23511889        -73.961902      40.803524
  try:
    parts = line.split('\t')
    (junk, id, lon, lat) = parts[0], parts[1], parts[2], parts[3]
    cur = conn.cursor()
    cur.execute("""SELECT %s FROM "%s" WHERE ST_CONTAINS(geom, ST_Transform(ST_GeomFromText('POINT(%s %s)', %s), %s))""" % (ID_COL, TABLE, lon, lat, FROM_SRID, TABLE_SRID))
    rows = cur.fetchall()

    if len(rows) == 0:
      print "no blocks found for %s %s" % (lat, lon)

    for row in rows:
      counts[row[0]][id] += 1
  except:
    print "bad line: " + line
    import traceback
    print traceback.print_exc()

c = 0
for blockid in counts:
  for woeid in counts[blockid]:
    c += 1
    cur = conn.cursor()
    cur.execute("""SELECT * FROM """ + VOTE_TABLE + """ WHERE id=%s AND label=%s AND source='flickr'""", (
      blockid, woeid))
    if len(cur.fetchall()) == 0:
        cur = conn.cursor()
        cur.execute("""INSERT INTO """ + VOTE_TABLE + """ (id, label, count, source) VALUES (%s, %s, %s, 'flickr');""", (
          blockid, woeid, counts[blockid][woeid]))
    else:
        print 'already had row for flickr %s %s' % (blockid, woeid)

    print "%s\t%s\t%s" % (blockid, woeid, counts[blockid][woeid])
    if (c % 1000) == 0:
      conn.commit()
conn.commit()
conn.close()
