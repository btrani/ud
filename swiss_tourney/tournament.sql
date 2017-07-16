-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

-- Create database
DROP DATABASE IF EXISTS tournament;
CREATE DATABASE tournament;

-- Connect to database
\c tournament;

-- Create table to hold player info
CREATE TABLE players (
	p_id serial PRIMARY KEY,
	name VARCHAR NOT NULL
);

-- Create table to hold match results
CREATE TABLE matches (
	m_id serial PRIMARY KEY,
	winner INT REFERENCES players(p_id) NOT NULL,
	loser INT REFERENCES players(p_id) NOT NULL
);