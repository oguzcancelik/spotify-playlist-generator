import os
from dotenv import load_dotenv, find_dotenv
import json
import spotipy
import spotipy.util as util
from json.decoder import JSONDecodeError
import sqlite3
from spotify import set_tracks, overwrite_playlist, add_to_playlist


def find_genre_songs():
    c.execute("""select distinct genre_name from artist_genre where genre_name not in
    (select distinct genre_name from genre_popular_tracks )""")
    genres = c.fetchall()
    counter = 1
    result = []
    for genre in genres:
        if counter % 10 == 0:
            updatetoken()
        counter += 1
        tracks = spotify.recommendations(seed_genres=[genre[0]], limit=50)
        result += [(genre[0], track['id'], track['artists'][0]['name']) for track in tracks['tracks']]
    if not result:
        return
    print(result)
    with connection:
        c.executemany("""INSERT INTO genre_popular_tracks VALUES(?,?,?)""", result)
    result.clear()


def find_artist_genre():
    c.execute("""SELECT DISTINCT artist_id FROM track WHERE artist_name NOT IN
            (SELECT DISTINCT artist_name FROM artist_genre)""")
    artists = c.fetchall()
    artist_ids = [x[0] for x in artists]
    artists.clear()
    for i in range(0, len(artist_ids), 50):
        artists += spotify.artists(artist_ids[i:i + 50])['artists']
    result = []
    for artist in artists:
        if artist['genres']:
            result += [(artist['name'], genre) for genre in artist['genres']]
    if not result:
        return
    print(result)
    with connection:
        c.executemany("""INSERT INTO artist_genre VALUES (?, ?)""", result)


def delete_duplicates_track():
    c.execute("""SELECT * FROM track GROUP BY artist_name, track_id HAVING COUNT(*) > 1""")
    result = c.fetchall()
    if not result:
        print("\nNo duplicate songs\n")
        return
    delete_tracks = []
    insert_tracks = []
    for i in result:
        print(i[2], "-", i[4])
        delete_tracks.append((i[0],))
        insert_tracks.append((i[0], i[1], i[2], i[3], i[4]))
    with connection:
        c.executemany("""DELETE FROM track where track_id=?""", delete_tracks)
        c.executemany("""INSERT INTO track VALUES (?,?,?,?,?)""", insert_tracks)
    delete_tracks.clear()
    insert_tracks.clear()


def delete_duplicates_similarartists():
    c.execute("""SELECT * FROM similar_artists GROUP BY artist_name, similar_artist_id HAVING COUNT(*) > 1""")
    result = c.fetchall()
    if not result:
        print("\nNo duplicate songs\n")
        return
    delete_tracks = []
    insert_tracks = []
    for i in result:
        print(i[0], "-", i[1])
        delete_tracks.append((i[0],))
        insert_tracks.append((i[0], i[1]))
    with connection:
        c.executemany("""DELETE FROM similar_artists where artist_name=?""", delete_tracks)
        c.executemany("""INSERT INTO similar_artists VALUES (?,?)""", insert_tracks)
    delete_tracks.clear()
    insert_tracks.clear()


def delete_duplicates_songinfo():
    c.execute("""SELECT * FROM song_info GROUP BY artist_name, track_id HAVING COUNT(*) > 1""")
    result = c.fetchall()
    if not result:
        print("\nNo duplicate songs\n")
        return
    delete_tracks = []
    insert_tracks = []
    for i in result:
        print(i[3], "-", i[1])
        delete_tracks.append((i[0],))
        insert_tracks.append((i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9], i[10], i[11], i[12], i[13],
                              i[14], i[15], i[16]))
    with connection:
        c.executemany("""DELETE FROM song_info where track_id=?""", delete_tracks)
        c.executemany("""INSERT INTO song_info VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", insert_tracks)
    delete_tracks.clear()
    insert_tracks.clear()


def get_top_tracks():
    long_term = spotify.current_user_top_tracks(limit=50, time_range="long_term")
    medium_term = spotify.current_user_top_tracks(limit=50, time_range="medium_term")
    short_term = spotify.current_user_top_tracks(limit=50, time_range="short_term")
    tracks = long_term['items'] + medium_term['items'] + short_term['items']
    insert_tracks = []
    for i in tracks:
        c.execute("""select count(track_id) from user_top_tracks where track_id=? and username=?""",
                  (i['id'], spotify_username))
        count = c.fetchone()[0]
        if count != 0:
            continue
        print(i['artists'][0]['name'], " - ", i['name'])
        features = spotify.audio_features(i['id'])
        features = features[0]
        insert_tracks.append((i['id'], i['name'], i['artists'][0]['id'], i['artists'][0]['name'], spotify_username,
                              features['acousticness'], features['danceability'], features['energy'],
                              features['duration_ms'],
                              features['instrumentalness'], features['key'], features['liveness'], features['loudness'],
                              features['mode'], features['speechiness'], features['tempo'], features['time_signature'],
                              features['valence'], i['popularity']))
    with connection:
        c.executemany("""INSERT INTO user_top_tracks VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                      insert_tracks)
    insert_tracks.clear()


def get_songs(artist_name=""):
    # c.execute("""select track_id,track_name,artist_id,artist_name from  track where artist_name in
    #         (SELECT DISTINCT artist_name from artist_genre where genre_name LIKE '%%' and
    #         artist_name not in(select distinct artist_name from song_info) order by random() LIMIT 150)""")
    c.execute("""select track_id,track_name,artist_id,artist_name from  track where artist_name not in
                (select distinct artist_name from song_info) """)
    # ,(artist_name,))
    tracks = c.fetchall()
    track_ids = [x[0] for x in tracks]
    counter = 0
    insert_tracks = []
    for i in range(0, len(track_ids), 50):
        features = spotify.audio_features(track_ids[i:i + 50])
        if counter % 8 == 0:
            updatetoken()
        counter += 1
        for j in range(0, len(features)):
            k = tracks[i + j]
            m = features[j]
            print(int(i / 50), " ", k[3], "-", k[1])
            if not m:
                with open("notfound.log", "a") as f:
                    f.write(k[3] + " - " + k[1] + "\n")
                continue
            insert_tracks.append(
                (k[0], k[1], k[2], k[3], m['acousticness'], m['danceability'], m['energy'], m['duration_ms'],
                 m['instrumentalness'], m['key'], m['liveness'], m['loudness'], m['mode'], m['speechiness'],
                 m['tempo'], m['time_signature'], m['valence']))
    with connection:
        c.executemany("""INSERT INTO song_info VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", insert_tracks)
    insert_tracks.clear()
    # print(json.dumps(result, sort_keys=True, indent=4))
    quit()


def find_similar_song(artist, song_name):
    # c.execute("""SELECT track_name from song_info order by random() limit 1""")
    # song_name = c.fetchone()[0]
    # song_name = "Kimseye Etmem Şikayet"
    # song_name = song_name + "%"
    c.execute(
        """select * from song_info where track_name LIKE ? COLLATE NOCASE and artist_name LIKE ? COLLATE NOCASE""",
        (song_name, artist))
    # c.execute("""select * from song_info order by random() limit 1""")
    #       c.execute(
    #       """select * from song_info where artist_name LIKE ? COLLATE NOCASE and (track_name LIKE ? COLLATE NOCASE
    #        or (track_name not like ? COLLATE NOCASE and track_name like ? COLLATE NOCASE )""",(artist,song_name2,song_name,song_name3,))

    i = c.fetchone()
    if not i:
        print('Song not found')
        quit()
    print("Song is:", i[3], "-", i[1])
    print("\n")
    c.execute("""select track_id,track_name,artist_name from song_info where acousticness > ? and acousticness < ? and 
                                               danceability > ? and danceability < ? and 
                                               energy > ? and energy < ?  and 
                                               instrumentalness > ? and instrumentalness < ?  and 
                                               liveness > ? and liveness < ?  and 
                                               loudness > ? and loudness < ?  and 
                                               speechiness > ? and speechiness < ?  and 
                                               tempo > ? and tempo < ? and
                                               valence > ? and valence < ? and 
                                               key > ? and key < ? and mode = ? and 
                                               time_signature = ? 
                                               group by artist_name, track_name order by random() limit 50""",
              (i[4] - 0.1, i[4] + 0.1,
               i[5] - 0.1, i[5] + 0.1,
               i[6] - 0.1, i[6] + 0.1,
               i[8] - 0.01, i[8] + 0.1,
               i[10] - 0.1, i[10] + 0.1,
               i[11] - 10, i[11] + 10,
               i[13] - 0.1, i[13] + 0.1,
               i[14] - 10, i[14] + 10,
               i[16] - 0.10, i[16] + 0.1,
               i[9] - 1, i[9] + 1,
               i[12], i[15],))
    result = c.fetchall()
    songs = []
    for j in result:
        print(j[2], "-", j[1])
        songs.append(j[0])
    set_tracks(songs)
    overwrite_playlist(song_name)


def get_by_genre():
    c.execute("""select track_id,track_name,artist_name from track where artist_name in (select distinct artist_name from artist_genre
                where genre_name LIKE '%turkish pop%' COLLATE NOCASE) ORDER BY RANDOM() LIMIT 200""")
    result = c.fetchall()
    songs = []
    for j in result:
        print(j[2], "-", j[1])
        songs.append(j[0])
    set_tracks(songs)
    # overwrite_playlist("TR")
    add_to_playlist("TR")


def updatetoken():
    global spotify, token
    try:
        token = util.prompt_for_user_token(spotify_username, scope, client_id, client_secret, redirect_uri)
    except(AttributeError, JSONDecodeError):
        os.remove(f".cache-{spotify_username}")
        token = util.prompt_for_user_token(spotify_username, scope, client_id, client_secret, redirect_uri)
    spotify = spotipy.Spotify(auth=token)


dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

client_id = os.environ.get("client_id")
client_secret = os.environ.get("client_secret")
redirect_uri = os.environ.get("redirect_uri")
spotify_username = os.environ.get("spotify_username")
scope = 'user-read-private ' \
        'user-read-playback-state ' \
        'user-modify-playback-state ' \
        'playlist-modify-public ' \
        'playlist-modify-private ' \
        'user-read-recently-played ' \
        'user-top-read ' \
        'playlist-read-private'

try:
    token = util.prompt_for_user_token(spotify_username, scope, client_id, client_secret, redirect_uri)
except(AttributeError, JSONDecodeError):
    os.remove(f".cache-{spotify_username}")
    token = util.prompt_for_user_token(spotify_username, scope, client_id, client_secret, redirect_uri)
spotify = spotipy.Spotify(auth=token)

connection = sqlite3.connect('spotify.sqlite3')
c = connection.cursor()
#
while True:
    print("1 - get songs")
    print("2 - find similar songs")
    print("3 - find artist genre")
    print("4 - find genre songs")
    print("5 - delete duplicates song_info")
    print("6 - delete duplicates track")
    print("7 - delete duplicates artist_genre")
    print("8 - get by genre")
    choice = input("\nMake choice: ")
    if choice == '1':
        artist_name = input("\nEnter artist name: ")
        get_songs(artist_name)
    elif choice == '2':
        artist_name = input("\nEnter artist name: ")
        song = input("\nEnter song name: ")
        find_similar_song(artist_name, song)
    elif choice == '3':
        find_artist_genre()
    elif choice == '4':
        find_genre_songs()
    elif choice == '5':
        delete_duplicates_songinfo()
    elif choice == '6':
        delete_duplicates_track()
    elif choice == '7':
        delete_duplicates_similarartists()
    elif choice == '8':
        get_by_genre()
    else:
        break
