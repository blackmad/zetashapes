--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: votes; Type: TABLE; Schema: public; Owner: blackmad; Tablespace: 
--

CREATE TABLE votes (
    id character varying(100) NOT NULL,
    label character varying(100) NOT NULL,
    count integer,
    source character varying(100) NOT NULL,
    countyfp10 character varying(10),
    statefp10 character varying(10)
);


ALTER TABLE public.votes OWNER TO blackmad;

--
-- Name: votes_pkey; Type: CONSTRAINT; Schema: public; Owner: blackmad; Tablespace: 
--

ALTER TABLE ONLY votes
    ADD CONSTRAINT votes_pkey PRIMARY KEY (id, label, source);


--
-- PostgreSQL database dump complete
--

