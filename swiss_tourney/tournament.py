#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    conn = psycopg2.connect("dbname=tournament")
    cur = conn.cursor()
    return conn, cur


def deleteMatches():
    """Remove all the match records from the database."""
    conn, cur = connect()
    q = ("DELETE FROM matches;")
    cur.execute(q)
    conn.commit()
    conn.close()


def deletePlayers():
    """Remove all the player records from the database."""
    conn, cur = connect()
    q = ("DELETE FROM players;")
    cur.execute(q)
    conn.commit()
    conn.close()


def countPlayers():
    """Returns the number of players currently registered."""
    conn, cur = connect()
    q = ("SELECT COUNT(p_id) FROM players")
    cur.execute(q)
    p_count = cur.fetchone()[0]
    conn.close()
    return p_count


def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    conn, cur = connect()
    q = ("INSERT INTO players(p_id, name) VALUES (default, %s);")
    cur.execute(q, (name,))
    conn.commit()
    conn.close()


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    conn, cur = connect()
    q = ('''
        WITH w AS (
            SELECT
                p.p_id,
                COUNT(*) AS wins
            FROM players p
            INNER JOIN matches m
            ON p.p_id = m.winner
            GROUP BY 1
        ),
        m AS (
            SELECT
                p.p_id,
                COUNT(*) AS matches
            FROM players p
            INNER JOIN matches m
            ON p.p_id = m.winner OR p.p_id = m.loser
            GROUP BY 1
        )
        SELECT
            p.p_id,
            p.name,
            COALESCE(w.wins, 0) AS wins,
            COALESCE(m.matches, 0) AS matches
        FROM players p
        LEFT JOIN w
        ON p.p_id = w.p_id
        LEFT JOIN m
        ON p.p_id = m.p_id
        ORDER BY 3 DESC, 4 DESC;
        '''
        )
    cur.execute(q)
    matches = cur.fetchall()
    conn.close()
    return matches



def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    conn, cur = connect()
    q = ("INSERT INTO matches(m_id, winner, loser) VALUES (default, %s, %s);")
    cur.execute(q, (winner, loser,))
    conn.commit()
    conn.close()
 
 
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    p_list = playerStandings()
    pairing = []
    if len(p_list) % 2 == 0:
        for i in range(0, len(p_list), 2):
            s = p_list[i][0], p_list[i][0], p_list[i+1][0], p_list[i+1][0]
            pairing.append(s)
        return pairing
    else:
        print "A Swiss Tournament Requires an Even Number of Players"


