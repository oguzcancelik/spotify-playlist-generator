import os
from dotenv import load_dotenv, find_dotenv
import spotipy
import spotipy.util as util
from spotipy import SpotifyException
import json
from json.decoder import JSONDecodeError
import random
import sqlite3


def select_songs(song_number):
    global artist_tracks, recommended_tracks
    for i in range(song_number):
        if artist_tracks:
            randon_number = random.randint(0, len(artist_tracks) - 1)
            recommended_tracks.append(artist_tracks[randon_number])
            del artist_tracks[randon_number]


def get_tracks(album_ids):
    global artist_tracks
    albums = []
    tracks = []
    for i in range(0, len(album_ids), 20):
        albums += spotify.albums(album_ids[i:i + 20])['albums']
    for album in albums:
        for track in album['tracks']['items']:
            tracks.append((track['id'], track['artists'][0]['id'], track['artists'][0]['name'],
                           album['release_date'][0:4], track['name']))
            artist_tracks.append(track['id'])
    try:
        with connection:
            c.executemany("""INSERT INTO track VALUES(?,?,?,?,?)""", tracks)
    except sqlite3.IntegrityError:
        pass
    tracks.clear()


def get_albums(artist_id):
    types = [["album", 50], ["single", 20], ["compilation", 10]]
    album_ids = []
    for album_type in types:
        albums = spotify.artist_albums(artist_id=artist_id, album_type=album_type[0], limit=album_type[1])
        album_ids += [album['id'] for album in albums['items']]
    get_tracks(album_ids)


def get_by_artist(artist, song_number=30):
    global artist_tracks, recommended_tracks
    c.execute("""SELECT track_id FROM track WHERE artist_name=? COLLATE NOCASE OR artist_id=?
              COLLATE NOCASE ORDER BY RANDOM() LIMIT ?""", (artist.upper(), artist.upper(), song_number))
    artist_tracks = c.fetchall()
    if artist_tracks:
        recommended_tracks += [x[0] for x in artist_tracks]
        return True
    try:
        artist_result = spotify.artist(artist)
        if artist_result['genres']:
            genres = [(artist_result['name'], genre) for genre in artist_result['genres']]
            with connection:
                c.executemany("""INSERT INTO artist_genre VALUES (?, ?)""", genres)
    except SpotifyException:
        artist = spotify.search(artist, 1, 0, "artist")
        if artist['artists']['total'] > 0:
            artist = artist['artists']['items'][0]['id']
        else:
            return False
    get_albums(artist)
    select_songs(song_number)
    artist_tracks.clear()
    return True


def get_by_related_artists(artist_name):
    c.execute("SELECT similar_artist_id FROM similar_artists WHERE artist_name=? COLLATE NOCASE",
              (artist_name.upper(),))
    related_artists = c.fetchall()
    if related_artists:
        for artist in related_artists:
            get_by_artist(artist[0], 5)
        return True
    artist = spotify.search(artist_name, 1, 0, "artist")
    if artist['artists']['total'] > 0:
        related_artists = spotify.artist_related_artists(artist['artists']['items'][0]['id'])
        if related_artists['artists']:
            related_artists['artists'].append(
                {'id': artist['artists']['items'][0]['id'], 'name': artist['artists']['items'][0]['name']})
            similar_artists = []
            for related_artist in related_artists['artists']:
                similar_artists.append((artist['artists']['items'][0]['name'], related_artist['id']))
                get_by_artist(related_artist['id'], 5)
                update_token()
            with connection:
                c.executemany("""INSERT INTO similar_artists VALUES(?,?)""", similar_artists)
            similar_artists.clear()
            return True
    return False


def get_by_top_artists(term):
    top_artists = spotify.current_user_top_artists(limit=20, offset=0, time_range=term)
    if top_artists['total'] > 0:
        for artist in top_artists['items']:
            get_by_artist(artist['id'], 5)
        return True
    return False


def get_by_recently_played():
    recently_played_artists = []
    recently_played_tracks = spotify.current_user_recently_played()
    if recently_played_tracks['items']:
        for track in recently_played_tracks['items']:
            artist_id = track['track']['artists'][0]['id']
            if artist_id not in recently_played_artists:
                recently_played_artists.append(artist_id)
                get_by_artist(artist_id, 2)
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


def get_by_new_releases():
    global artist_tracks
    new_releases = spotify.new_releases(country="TR")
    if new_releases['albums']['total'] > 0:
        album_ids = [album['id'] for album in new_releases['albums']['items']]
        get_tracks(album_ids)
        select_songs(40)
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
    c.execute("""SELECT track_id FROM track WHERE track_name LIKE '%(Live%' COLLATE NOCASE OR  
    	track_name LIKE '%live from%' COLLATE NOCASE ORDER BY RANDOM() LIMIT 50""")
    tracks = c.fetchall()
    if tracks:
        recommended_tracks = [x[0] for x in tracks]
        return True
    return False

def get_acoustic_tracks():
    global recommended_tracks
    c.execute("""SELECT track_id FROM track WHERE track_name LIKE '%acoustic%' COLLATE NOCASE OR  
    	track_name LIKE '%akustik%' COLLATE NOCASE ORDER BY RANDOM() LIMIT 50""")
    tracks = c.fetchall()
    if tracks:
        recommended_tracks = [x[0] for x in tracks]
        return True
    return False


def get_by_playlist(playlist_name):
    get_user_playlists()
    playlists_id = get_playlist_id(playlist_name, 0)
    if playlist_id == "":
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
        random.shuffle(recommended_tracks)
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
spotify = None
update_token()

connection = sqlite3.connect('spotify.sqlite3')
c = connection.cursor()

artist_tracks = []
recommended_tracks = []
playlists = []
playlist_id = ""

# print(json.dumps(artist, sort_keys=True, indent=4))
# quit()
