DROP TABLE IF EXISTS geoplanet_places;
CREATE TABLE geoplanet_places
(
  woe_id integer NOT NULL,
  iso character varying(2) NOT NULL,
  "name" character varying(150) NOT NULL,
  "language" character varying(3) NOT NULL,
  placetype character varying(20) NOT NULL,
  parent_id integer NOT NULL,
  CONSTRAINT places_pkey PRIMARY KEY (woe_id)
);
