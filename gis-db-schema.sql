--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry, geography, and raster spatial types and functions';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: area_counts; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE area_counts (
    areaid character varying(100),
    count integer
);


ALTER TABLE public.area_counts OWNER TO postgres;

--
-- Name: connections; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE connections (
    id integer NOT NULL,
    user_id integer,
    provider_id character varying(255),
    provider_user_id character varying(255),
    access_token character varying(255),
    secret character varying(255),
    display_name character varying(255),
    profile_url character varying(512),
    image_url character varying(512),
    rank integer
);


ALTER TABLE public.connections OWNER TO postgres;

--
-- Name: connections_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE connections_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.connections_id_seq OWNER TO postgres;

--
-- Name: connections_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE connections_id_seq OWNED BY connections.id;


--
-- Name: geoname; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE geoname (
    geonameid integer,
    name character varying(200),
    asciiname character varying(200),
    alternatenames character varying(8000),
    latitude double precision,
    longitude double precision,
    fclass character(1),
    fcode character varying(10),
    country character varying(2),
    cc2 character varying(60),
    admin1 character varying(20),
    admin2 character varying(80),
    admin3 character varying(20),
    admin4 character varying(20),
    population bigint,
    elevation integer,
    gtopo30 integer,
    timezone character varying(40),
    moddate date
);


ALTER TABLE public.geoname OWNER TO postgres;

--
-- Name: geoplanet_places; Type: TABLE; Schema: public; Owner: blackmad; Tablespace: 
--

CREATE TABLE geoplanet_places (
    woe_id integer NOT NULL,
    iso character varying(2) NOT NULL,
    name character varying(150) NOT NULL,
    language character varying(3) NOT NULL,
    placetype character varying(20) NOT NULL,
    parent_id integer NOT NULL
);


ALTER TABLE public.geoplanet_places OWNER TO blackmad;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE roles (
    id integer NOT NULL,
    name character varying(80),
    description character varying(255)
);


ALTER TABLE public.roles OWNER TO postgres;

--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE roles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.roles_id_seq OWNER TO postgres;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE roles_id_seq OWNED BY roles.id;


--
-- Name: roles_users; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE roles_users (
    user_id integer,
    role_id integer
);


ALTER TABLE public.roles_users OWNER TO postgres;

--
-- Name: tabblock10; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE tabblock10 (
    gid integer NOT NULL,
    statefp10 character varying(2),
    countyfp10 character varying(3),
    tractce10 character varying(6),
    blockce10 character varying(4),
    geoid10 character varying(15),
    name10 character varying(10),
    mtfcc10 character varying(5),
    ur10 character varying(1),
    uace10 character varying(5),
    uatyp10 character varying(1),
    funcstat10 character varying(1),
    aland10 double precision,
    awater10 double precision,
    intptlat10 character varying(11),
    intptlon10 character varying(12),
    geom geometry(MultiPolygon)
);


ALTER TABLE public.tabblock10 OWNER TO postgres;

--
-- Name: tabblock10_gid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE tabblock10_gid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tabblock10_gid_seq OWNER TO postgres;

--
-- Name: tabblock10_gid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE tabblock10_gid_seq OWNED BY tabblock10.gid;


--
-- Name: tl_2010_us_county10; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE tl_2010_us_county10 (
    gid integer NOT NULL,
    statefp10 character varying(2),
    countyfp10 character varying(3),
    countyns10 character varying(8),
    geoid10 character varying(5),
    name10 character varying(100),
    namelsad10 character varying(100),
    lsad10 character varying(2),
    classfp10 character varying(2),
    mtfcc10 character varying(5),
    csafp10 character varying(3),
    cbsafp10 character varying(5),
    metdivfp10 character varying(5),
    funcstat10 character varying(1),
    aland10 double precision,
    awater10 double precision,
    intptlat10 character varying(11),
    intptlon10 character varying(12),
    geom geometry(MultiPolygon,4326)
);


ALTER TABLE public.tl_2010_us_county10 OWNER TO postgres;

--
-- Name: tl_2010_us_county10_gid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE tl_2010_us_county10_gid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tl_2010_us_county10_gid_seq OWNER TO postgres;

--
-- Name: tl_2010_us_county10_gid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE tl_2010_us_county10_gid_seq OWNED BY tl_2010_us_county10.gid;


--
-- Name: tl_2010_us_state10; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE tl_2010_us_state10 (
    gid integer NOT NULL,
    region10 character varying(2),
    division10 character varying(2),
    statefp10 character varying(2),
    statens10 character varying(8),
    geoid10 character varying(2),
    stusps10 character varying(2),
    name10 character varying(100),
    lsad10 character varying(2),
    mtfcc10 character varying(5),
    funcstat10 character varying(1),
    aland10 double precision,
    awater10 double precision,
    intptlat10 character varying(11),
    intptlon10 character varying(12),
    geom geometry(MultiPolygon,4326)
);


ALTER TABLE public.tl_2010_us_state10 OWNER TO postgres;

--
-- Name: tl_2010_us_state10_gid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE tl_2010_us_state10_gid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tl_2010_us_state10_gid_seq OWNER TO postgres;

--
-- Name: tl_2010_us_state10_gid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE tl_2010_us_state10_gid_seq OWNED BY tl_2010_us_state10.gid;


--
-- Name: user_votes; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE user_votes (
    userid integer,
    blockid character varying(15),
    woe_id integer,
    ts timestamp without time zone,
    weight integer
);


ALTER TABLE public.user_votes OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE users (
    id integer NOT NULL,
    email character varying(255),
    password character varying(120),
    active boolean,
    last_login_at timestamp without time zone,
    current_login_at timestamp without time zone,
    last_login_ip character varying(100),
    current_login_ip character varying(100),
    login_count integer,
    api_key character varying(120),
    level integer DEFAULT 0
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE users_id_seq OWNED BY users.id;


--
-- Name: votes; Type: TABLE; Schema: public; Owner: blackmad; Tablespace: 
--

CREATE TABLE votes (
    id character varying(100) NOT NULL,
    label integer NOT NULL,
    count integer,
    source character varying(100) NOT NULL
);


ALTER TABLE public.votes OWNER TO blackmad;

--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY connections ALTER COLUMN id SET DEFAULT nextval('connections_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY roles ALTER COLUMN id SET DEFAULT nextval('roles_id_seq'::regclass);


--
-- Name: gid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tabblock10 ALTER COLUMN gid SET DEFAULT nextval('tabblock10_gid_seq'::regclass);


--
-- Name: gid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tl_2010_us_county10 ALTER COLUMN gid SET DEFAULT nextval('tl_2010_us_county10_gid_seq'::regclass);


--
-- Name: gid; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY tl_2010_us_state10 ALTER COLUMN gid SET DEFAULT nextval('tl_2010_us_state10_gid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);


--
-- Data for Name: spatial_ref_sys; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY spatial_ref_sys (srid, auth_name, auth_srid, srtext, proj4text) FROM stdin;
\.


--
-- Name: connections_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY connections
    ADD CONSTRAINT connections_pkey PRIMARY KEY (id);


--
-- Name: geoid_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tabblock10
    ADD CONSTRAINT geoid_uniq UNIQUE (geoid10);


--
-- Name: places_pkey; Type: CONSTRAINT; Schema: public; Owner: blackmad; Tablespace: 
--

ALTER TABLE ONLY geoplanet_places
    ADD CONSTRAINT places_pkey PRIMARY KEY (woe_id);


--
-- Name: roles_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: tabblock10_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tabblock10
    ADD CONSTRAINT tabblock10_pkey PRIMARY KEY (gid);


--
-- Name: tl_2010_us_county10_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tl_2010_us_county10
    ADD CONSTRAINT tl_2010_us_county10_pkey PRIMARY KEY (gid);


--
-- Name: tl_2010_us_state10_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY tl_2010_us_state10
    ADD CONSTRAINT tl_2010_us_state10_pkey PRIMARY KEY (gid);


--
-- Name: users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: votes_pkey; Type: CONSTRAINT; Schema: public; Owner: blackmad; Tablespace: 
--

ALTER TABLE ONLY votes
    ADD CONSTRAINT votes_pkey PRIMARY KEY (id, label, source);


--
-- Name: woeid_uniq; Type: CONSTRAINT; Schema: public; Owner: blackmad; Tablespace: 
--

ALTER TABLE ONLY geoplanet_places
    ADD CONSTRAINT woeid_uniq UNIQUE (woe_id);


--
-- Name: geoname_geonameid_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX geoname_geonameid_idx ON geoname USING btree (geonameid);


--
-- Name: tabblock10_geom_gist; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX tabblock10_geom_gist ON tabblock10 USING gist (geom);


--
-- Name: tabblock10_statefp10_countyfp10_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX tabblock10_statefp10_countyfp10_idx ON tabblock10 USING btree (statefp10, countyfp10);


--
-- Name: tl_2010_us_county10_geom_gist; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX tl_2010_us_county10_geom_gist ON tl_2010_us_county10 USING gist (geom);


--
-- Name: tl_2010_us_state10_geom_gist; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX tl_2010_us_state10_geom_gist ON tl_2010_us_state10 USING gist (geom);


--
-- Name: user_votes_blockid_userid_idx; Type: INDEX; Schema: public; Owner: postgres; Tablespace: 
--

CREATE INDEX user_votes_blockid_userid_idx ON user_votes USING btree (blockid, userid);


--
-- Name: votes_id_idx; Type: INDEX; Schema: public; Owner: blackmad; Tablespace: 
--

CREATE INDEX votes_id_idx ON votes USING btree (id);


--
-- Name: geometry_columns_delete; Type: RULE; Schema: public; Owner: postgres
--

CREATE RULE geometry_columns_delete AS ON DELETE TO geometry_columns DO INSTEAD NOTHING;


--
-- Name: geometry_columns_insert; Type: RULE; Schema: public; Owner: postgres
--

CREATE RULE geometry_columns_insert AS ON INSERT TO geometry_columns DO INSTEAD NOTHING;


--
-- Name: geometry_columns_update; Type: RULE; Schema: public; Owner: postgres
--

CREATE RULE geometry_columns_update AS ON UPDATE TO geometry_columns DO INSTEAD NOTHING;


--
-- Name: connections_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY connections
    ADD CONSTRAINT connections_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: roles_users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY roles_users
    ADD CONSTRAINT roles_users_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id);


--
-- Name: roles_users_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY roles_users
    ADD CONSTRAINT roles_users_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: user_votes_blockid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY user_votes
    ADD CONSTRAINT user_votes_blockid_fkey FOREIGN KEY (blockid) REFERENCES tabblock10(geoid10);


--
-- Name: user_votes_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY user_votes
    ADD CONSTRAINT user_votes_userid_fkey FOREIGN KEY (userid) REFERENCES users(id);


--
-- Name: user_votes_woe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY user_votes
    ADD CONSTRAINT user_votes_woe_id_fkey FOREIGN KEY (woe_id) REFERENCES geoplanet_places(woe_id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

