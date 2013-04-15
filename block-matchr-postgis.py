#!/usr/bin/python

import psycopg2
from collections import defaultdict

# SELECT * FROM "tabblock2010_36_pophu-900913" WHERE ST_CONTAINS(geom, ST_Transform(ST_GeomFromText('POINT(-74 40.74)', 4326), 900913));

import sys

ID_COL = 'blockid10'
TABLE = 'tabblock2010_36_pophu-900913'
TABLE_SRID = 900913

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
    cur.execute("""SELECT %s FROM "%s" WHERE ST_CONTAINS(geom, ST_Transform(ST_GeomFromText('POINT(%s %s)', 4326), %s))""" % (ID_COL, TABLE, lon, lat, TABLE_SRID))
    rows = cur.fetchall()

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
    cur.execute("""INSERT INTO votes2(id, label, count, source) VALUES (%s, %s, %s, 'flickr');""", (
      blockid, woeid, counts[blockid][woeid]))
#    print "%s\t%s\t%s" % (blockid, woeid, counts[blockid][woeid])
    if (c % 1000) == 0:
      conn.commit()
conn.commit()
conn.close()
