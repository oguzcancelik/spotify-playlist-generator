import sqlite3

connection = sqlite3.connect('spotify.sqlite3')
c = connection.cursor()

c.execute("""CREATE TABLE track (
    track_id text,
    artist_id text,
    artist_name text,
    release_date text,
    track_name text
    )""")

c.execute("""CREATE TABLE similar_artists (
    artist_name text,
    similar_artist_id text
    )""")

c.execute("""CREATE TABLE similar_tracks(
    track_name text,
    artist_name text,
    similar_track_id text
    )""")

c.execute("""CREATE TABLE artist_genre(
    artist_name text,
    genre_name text
    )""")

c.execute("""CREATE TABLE genre_popular_tracks(
    genre_name text,
    track_id text
    )""")

c.execute("""CREATE TABLE song_info(
	track_id text,
	track_name text,
	artist_id text,
	artist_name text,
	acousticness REAL,
	danceability REAL,
	energy REAL,
	duration_ms INTEGER,
	instrumentalness REAL,
	key INTEGER,
	liveness REAL,
	loudness REAL,
	mode INTEGER,
	speechiness REAL,
	tempo REAL,
	time_signature INTEGER,
	valence REAL
)""")

connection.commit()
connection.close()
