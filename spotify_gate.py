import os
from dotenv import load_dotenv, find_dotenv
import spotipy
import spotipy.util as util
import json
from json.decoder import JSONDecodeError
import random
import sqlite3
import logging


def select_songs(song_number):
    global artist_tracks, recommended_tracks
    for i in range(song_number):
        if artist_tracks:
            random_number = random.randint(0, len(artist_tracks) - 1)
            recommended_tracks.append(artist_tracks[random_number])
            del artist_tracks[random_number]
    random.shuffle(recommended_tracks)


def get_tracks(album_ids, write_to_db=True):
    global artist_tracks, logger
    albums = []
    tracks = []
    for i in range(0, len(album_ids), 20):
        albums += spotify.albums(album_ids[i:i + 20])['albums']
    for album in albums:
        logger.info("ALBUM - Getting: " + album['artists'][0]['name'] + " - " + album['name'])
        for track in album['tracks']['items']:
            tracks.append((track['id'], track['artists'][0]['id'], track['artists'][0]['name'],
                           album['release_date'][0:4], track['name']))
            artist_tracks.append(track['id'])
    if tracks and write_to_db:
        with connection:
            c.executemany("""INSERT INTO track VALUES(?,?,?,?,?)""", tracks)
        tracks.clear()


def get_albums(artist_id):
    types = [["album", 50], ["single", 20], ["compilation", 10]]
    album_ids = []
    for album_type in types:
        albums = spotify.artist_albums(artist_id=artist_id, album_type=album_type[0], limit=album_type[1])
        album_ids += [album['id'] for album in albums['items']]
    get_tracks(album_ids)


def get_by_artist(artist_name=None, artist_id=None, song_number=30):
    global artist_tracks, recommended_tracks, logger
    if artist_name:
        c.execute("""SELECT track_id FROM track WHERE artist_name LIKE ? COLLATE NOCASE ORDER BY RANDOM() LIMIT ?""",
                  (artist_name.upper(), song_number))
    else:
        c.execute("""SELECT track_id FROM track WHERE artist_id LIKE ? ORDER BY RANDOM() LIMIT ?""",
                  (artist_id, song_number))
    artist_tracks = c.fetchall()
    if artist_tracks:
        recommended_tracks += [x[0] for x in artist_tracks]
        return True
    if not artist_id:
        artist = spotify.search(artist_name, 1, 0, "artist")
        if artist['artists']['total'] > 0:
            artist_id = artist['artists']['items'][0]['id']
            logger.info("ARTIST - Getting by Name: " + artist['artists']['items'][0]['name'])
        else:
            logger.error("ARTIST - " + artist_name + " not found.")
            return False
    else:
        logger.info("ARTIST - Getting by ID: " + artist_id)
    get_albums(artist_id)
    select_songs(song_number)
    artist_tracks.clear()
    return True


def get_by_related_artists(artist_name):
    global logger
    c.execute("SELECT similar_artist_id FROM similar_artists WHERE artist_name=? COLLATE NOCASE",
              (artist_name.upper(),))
    related_artists = c.fetchall()
    if related_artists:
        for artist in related_artists:
            get_by_artist(artist_id=artist[0], song_number=5)
        return True
    artist = spotify.search(artist_name, 1, 0, "artist")
    if artist['artists']['total'] > 0:
        related_artists = spotify.artist_related_artists(artist['artists']['items'][0]['id'])
        if related_artists['artists']:
            logger.info("RELATED ARTISTS - Getting: " + artist['artists']['items'][0]['name'])
            related_artists['artists'].append(
                {'id': artist['artists']['items'][0]['id'], 'name': artist['artists']['items'][0]['name']})
            similar_artists = []
            for related_artist in related_artists['artists']:
                similar_artists.append((artist['artists']['items'][0]['name'], related_artist['id']))
                get_by_artist(artist_id=related_artist['id'], song_number=5)
                update_token()
            with connection:
                c.executemany("""INSERT INTO similar_artists VALUES(?,?)""", similar_artists)
            similar_artists.clear()
            return True
        logger.error("RELATED ARTISTS - Getting:" + artist_name + ": Related artists not found.")
        return False
    logger.error("ARTIST - " + artist_name + " not found.")
    return False


def get_by_top_artists(term):
    global logger
    top_artists = spotify.current_user_top_artists(limit=20, offset=0, time_range=term)
    if top_artists['total'] > 0:
        logger.info("TOP ARTISTS - Getting: " + spotify_username)
        for artist in top_artists['items']:
            get_by_artist(artist['id'], 5)
        return True
    logger.error("TOP ARTISTS - Can't get top artists: " + spotify_username)
    return False


def get_by_recently_played():
    global logger
    recently_played_artists = []
    recently_played_tracks = spotify.current_user_recently_played()
    if recently_played_tracks['items']:
        logger.info("RECENTLY PLAYED ARTISTS - Getting for " + spotify_username)
        for track in recently_played_tracks['items']:
            artist_id = track['track']['artists'][0]['id']
            if artist_id not in recently_played_artists:
                recently_played_artists.append(artist_id)
                get_by_artist(artist_id, 2)
        return True
    logger.error("RECENTLY PLAYED ARTISTS  - Can't get recently played artists: " + spotify_username)
    return False


def get_by_song(artist_name, track_name):
    global recommended_tracks, logger
    track = spotify.search(q=artist_name + " " + track_name, limit=1, type="track")
    if track['tracks']['items']:
        track_id = track['tracks']['items'][0]['id']
        tracks = spotify.recommendations(seed_tracks=[track_id], limit=50)
        if tracks['tracks']:
            recommended_tracks.append(track_id)
            recommended_tracks += [x['id'] for x in tracks['tracks']]
            return True
    return False


def get_all_genres():
    return spotify.recommendation_genre_seeds()['genres']


def get_by_genres(genres):
    global recommended_tracks
    c.execute("SELECT DISTINCT genre_name FROM genre_popular_tracks")
    stored_genres = [x[0] for x in c.fetchall()]
    genre_tracks = []
    for genre in genres:
        if genre in stored_genres:
            c.execute("SELECT track_id FROM genre_popular_tracks WHERE genre_name=? COLLATE NOCASE", (genre.upper(),))
            recommended_tracks += [x[0] for x in c.fetchall()]
            continue
        tracks = spotify.recommendations(limit=50, seed_genres=[genre])
        for track in tracks['tracks']:
            genre_tracks.append((genre, track['id'], track['artists'][0]['name']))
            recommended_tracks.append(track['id'])
    with connection:
        c.executemany("""INSERT INTO genre_popular_tracks VALUES(?,?,?)""", genre_tracks)
    genre_tracks.clear()
    if recommended_tracks:
        return True
    return False


def get_by_artist_genre(artist_name):
    global recommended_tracks
    c.execute("""SELECT t.track_id FROM track AS t,artist_genre AS g WHERE g.artist_name = t.artist_name AND 
              g.genre_name IN (SELECT genre_name FROM artist_genre WHERE artist_name=? COLLATE NOCASE or artist_name=? 
              COLLATE NOCASE or artist_name=? COLLATE NOCASE) GROUP BY t.artist_name ORDER BY RANDOM() LIMIT 50""",
              (artist_name.upper(), artist_name.lower(), " ".join(x.capitalize() for x in artist_name.split())))
    tracks = c.fetchall()
    if tracks:
        recommended_tracks = [x[0] for x in tracks]
        return True
    return False


def get_by_artist_recommendations(artist_name):
    global recommended_tracks
    artist = spotify.search(q=artist_name, limit=1, type="artist")
    if artist['artists']['items']:
        artist_id = artist['artists']['items'][0]['id']
        tracks = spotify.recommendations(seed_artists=[artist_id], limit=50)
        if tracks['tracks']:
            recommended_tracks += [x['id'] for x in tracks['tracks']]
            return True
    return False


def get_by_new_releases():
    global artist_tracks
    new_releases = spotify.new_releases()
    if new_releases['albums']['total'] > 0:
        album_ids = [album['id'] for album in new_releases['albums']['items']]
        get_tracks(album_ids=album_ids, write_to_db=False)
        select_songs(50)
        artist_tracks.clear()
        return True
    return False


def get_by_year(year):
    global recommended_tracks
    c.execute("""SELECT track_id FROM track WHERE release_date=? GROUP BY artist_name ORDER BY RANDOM() LIMIT 50""",
              (year,))
    tracks = c.fetchall()
    if tracks:
        recommended_tracks = [x[0] for x in tracks]
        return True
    return False


def get_live_tracks():
    global recommended_tracks
    c.execute("""SELECT track_id FROM track WHERE 
        track_name LIKE '%(Live%' COLLATE NOCASE OR 
        track_name LIKE '%live from%' COLLATE NOCASE OR 
        track_name LIKE '%live in%' COLLATE NOCASE OR
        track_name LIKE '%live at%' COLLATE NOCASE OR
        track_name LIKE '%- live%' COLLATE NOCASE
        ORDER BY RANDOM() LIMIT 50""")
    tracks = c.fetchall()
    if tracks:
        recommended_tracks = [x[0] for x in tracks]
        return True
    return False


def get_acoustic_tracks():
    global recommended_tracks
    c.execute("""SELECT track_id FROM track WHERE track_name LIKE '%acoustic%' COLLATE NOCASE OR track_name 
    LIKE '%akustik%' COLLATE NOCASE ORDER BY RANDOM() LIMIT 50""")
    tracks = c.fetchall()
    if tracks:
        recommended_tracks = [x[0] for x in tracks]
        return True
    return False


def get_random():
    global recommended_tracks
    c.execute("""SELECT track_id FROM track ORDER BY RANDOM() LIMIT 1000""")
    tracks = c.fetchall()
    if tracks:
        recommended_tracks = [x[0] for x in tracks]
        return True
    return False


def get_by_keyword(keyword):
    global recommended_tracks
    c.execute("""SELECT track_id FROM track WHERE track_name LIKE ? GROUP BY artist_name ORDER BY RANDOM() LIMIT 50""",
              ("%" + keyword + "%",))
    tracks = c.fetchall()
    if tracks:
        recommended_tracks = [x[0] for x in tracks]
        return True
    return False


def get_by_playlist(playlist_name):
    get_user_playlists()
    playlists_id = get_playlist_id(playlist_name, 0)
    if playlists_id is "":
        return False
    artist_names = []
    tracks = spotify.user_playlist_tracks(spotify_username, playlists_id, fields="items")
    for track in tracks['items']:
        artist_name = track['track']['artists'][0]['name']
        if artist_name not in artist_names:
            artist_names.append(artist_name)
    for i in range(5):
        randon_number = random.randint(0, len(artist_names) - 1)
        get_by_related_artists(artist_name=artist_names[randon_number])
        if len(artist_names) > 5:
            del artist_names[randon_number]
    return True


def get_user_playlists():
    global playlists
    user_playlists = spotify.current_user_playlists(limit=50, offset=0)
    for playlist in user_playlists['items']:
        if playlist['owner']['id'] == spotify_username:
            playlists.append({'id': playlist['id'], 'name': playlist['name'], 'track_num': playlist['tracks']['total']})


def get_playlist_id(playlist_name, choice=1):
    global playlists
    for playlist in playlists:
        if playlist_name == playlist['name']:
            if choice is 0 and not playlist['track_num'] > 0:
                return ""
            return playlist['id']
    if choice is 0:
        return ""
    playlist = spotify.user_playlist_create(spotify_username, playlist_name, public=False)
    return playlist['id']


def add_to_playlist(playlist_name, overwrite=False):
    global playlist_id
    if recommended_tracks:
        get_user_playlists()
        playlist_id = get_playlist_id(playlist_name)
        start_index = 0
        if overwrite:
            spotify.user_playlist_replace_tracks("", playlist_id, recommended_tracks[:100])
            start_index = 100
        for i in range(start_index, len(recommended_tracks), 100):
            spotify.user_playlist_add_tracks("", playlist_id, recommended_tracks[i:i + 100])


def delete_tracks():
    global recommended_tracks
    recommended_tracks.clear()


def set_tracks(songs):
    global recommended_tracks
    recommended_tracks = songs


def play():
    playlist_uri = spotify.user_playlist(user=spotify_username, playlist_id=playlist_id)
    devices = spotify.devices()
    if devices['devices'] and devices['devices'][0]['is_active']:
        spotify.start_playback(context_uri=playlist_uri['uri'])
        spotify.shuffle(state=True)
        return True
    return False


def update_token():
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
scope = os.environ.get("scope")

token = None
spotify = spotipy.Spotify
update_token()

connection = sqlite3.connect('spotify.sqlite3')
c = connection.cursor()

LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename="logger.log", level=logging.INFO, format=LOG_FORMAT, filemode="w")
logger = logging.getLogger()

artist_tracks = []
recommended_tracks = []
playlists = []
playlist_id = ""

# print(json.dumps("", sort_keys=True, indent=4, ensure_ascii=False))
# quit()
