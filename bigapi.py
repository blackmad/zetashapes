#!/usr/bin/python
# select COUNT(*) FROM "tabblock2010_36_pophu-900913" tb WHERE geom && ST_SetSRID(ST_MakeBox2D(ST_Transform(ST_GeomFromText('POINT(-74.13711547851562 40.526326510744006)', 4326), 900913), ST_Transform(ST_GeomFromText('POINT(-73.641357421875 40.90936126702326)', 4326), 900913)), 900913);
from flask import Flask
from flask.ext import restful
from flask.ext.restful import reqparse
import psycopg2
import psycopg2.extras
from collections import defaultdict

conn = psycopg2.connect("dbname='gis' user='blackmad' host='localhost' password='xxx'")

app = Flask(__name__)
api = restful.Api(app)

class HelloWorld(restful.Resource):
  def get(self):
    return {'hello': 'world'}

class CityData(restful.Resource):
  @staticmethod
  def makeFeature(row, voteDict):
    return {
      "type": "Feature",
      "geometry": eval(row['geojson_geom']),
      "properties": {
        "id": row['blockid10'],
        "votes": voteDict[row['blockid10']]
      }
    }

  @staticmethod
  def makeFeatures(rows, voteDict):
    return [CityData.makeFeature(r, voteDict) for r in rows]

  def get(self):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    parser = reqparse.RequestParser()
    parser.add_argument('countyfp10', type=str, help='countyfp10')
    parser.add_argument('statefp10', type=str, help='statefp10')
    args = parser.parse_args()

#    cur.execute("""select blockid10, ST_AsGeoJSON(ST_Transform(geom, 4326)) as geojson_geom FROM "tabblock2010_36_pophu-900913" tb WHERE geom && ST_SetSRID(ST_MakeBox2D(ST_Transform(ST_GeomFromText('POINT(-74.13711547851562 40.526326510744006)', 4326), 900913), ST_Transform(ST_GeomFromText('POINT(-73.641357421875 40.90936126702326)', 4326), 900913)), 900913)""")

    cur.execute("""select blockid10, ST_AsGeoJSON(ST_Transform(geom, 4326)) as geojson_geom FROM "tabblock2010_36_pophu-900913" tb WHERE statefp10 = %s AND countyfp10 = %s""", (args['statefp10'], args['countyfp10']))
    rows = cur.fetchall()

    cur.execute("""select id, label, count, source, name FROM votes2 v JOIN geoplanet ON label = woeid WHERE statefp10 = %s AND countyfp10 = %s""", (args['statefp10'], args['countyfp10']))
    votes = defaultdict(list)
    for r in cur.fetchall():
      votes[r['label']].append({
        'label': votes['name'], 
        'count': votes['count'], 
        'source': votes['source']
      })

    response = {
      "type": "FeatureCollection",
      "features": CityData.makeFeatures(rows, votes)
    }

    return response

api.add_resource(HelloWorld, '/')
api.add_resource(CityData, '/citydata')

if __name__ == '__main__':
  app.run(debug=True, 
   host='0.0.0.0'
  )
