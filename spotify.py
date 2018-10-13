import os
from dotenv import load_dotenv, find_dotenv
import spotipy
import spotipy.util as util
import json
from json.decoder import JSONDecodeError
import random
import pylast
import sqlite3

from spotipy import SpotifyException


def find_tracks_in_spotify():
    global last_fm_tracks
    for last_fm_track in last_fm_tracks:
        track = spotify.search(last_fm_track.item, 1, 0, "track")
        if track['tracks']['total'] > 0:
            recommended_tracks.append(track['tracks']['items'][0]['id'])
    if len(recommended_tracks) > 0:
        return True
    return False


def select_songs(song_number):
    global artist_tracks, recommended_tracks
    for i in range(song_number):
        if len(artist_tracks) > 0:
            randon_number = random.randint(0, len(artist_tracks) - 1)
            recommended_tracks.append(artist_tracks[randon_number])
            del artist_tracks[randon_number]


def get_tracks(album_id):
    global artist_tracks
    album = spotify.album(album_id)
    for track in album['tracks']['items']:
        with connection:
            c.execute("""INSERT INTO track VALUES(?,?,?,?,?)""",
                      (track['id'], track['artists'][0]['id'], track['artists'][0]['name'],
                       album['release_date'][0:4], track['name']))
        artist_tracks.append(track['id'])


def get_albums(artist_id):
    types = [["album", 50], ["single", 20], ["compilation", 10]]
    for album_type in types:
        albums = spotify.artist_albums(artist_id=artist_id, album_type=album_type[0], limit=album_type[1])
        for album in albums['items']:
            get_tracks(album['id'])


def get_by_artist(artist, song_number=30):
    global artist_tracks, recommended_tracks
    c.execute("""SELECT COUNT(track_id) FROM track WHERE artist_name=? OR artist_id=? COLLATE NOCASE""",
              (artist, artist))
    track_number = c.fetchone()[0]
    if track_number > 0:
        c.execute(
            "SELECT track_id FROM track WHERE artist_name=? OR artist_id=? COLLATE NOCASE ORDER BY RANDOM() LIMIT ?",
            (artist, artist, song_number))
        artist_tracks = c.fetchall()
        for x in artist_tracks:
            recommended_tracks.append(x[0])
        return True
    try:
        spotify.artist(artist)
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
    c.execute("""SELECT COUNT(similar_artist_id) FROM similar_artists WHERE artist_name=? COLLATE NOCASE""",
              (artist_name,))
    artist_number = c.fetchone()[0]
    if artist_number > 0:
        c.execute("SELECT similar_artist_id FROM similar_artists WHERE artist_name=? COLLATE NOCASE",
                  (artist_name,))
        related_artists = c.fetchall()
        for artist in related_artists:
            get_by_artist(artist[0], 5)
        return True
    artist = spotify.search(artist_name, 1, 0, "artist")
    if artist['artists']['total'] > 0:
        related_artists = spotify.artist_related_artists(artist['artists']['items'][0]['id'])
        if related_artists['artists']:
            related_artists['artists'].append({'id': artist['artists']['items'][0]['id']})
            for related_artist in related_artists['artists']:
                with connection:
                    c.execute("""INSERT INTO similar_artists VALUES(?,?)""",
                              (artist_name, related_artist['id']))
                get_by_artist(related_artist['id'], 5)
            return True
    return False


def get_by_top_artists(term):
    global artist_tracks
    top_artists = spotify.current_user_top_artists(limit=20, offset=0, time_range=term)
    if top_artists['total'] > 0:
        for artist in top_artists['items']:
            get_albums(artist['id'])
            select_songs(5)
            artist_tracks.clear()
        return True
    else:
        return False


def get_all_genres():
    return spotify.recommendation_genre_seeds()['genres']


def get_by_genres(genres):
    global recommended_tracks
    # all_genres = spotify.recommendation_genre_seeds()
    tracks = spotify.recommendations(limit=50, seed_genres=genres, country="TR")
    if len(tracks['tracks']) == 0:
        return False
    for track in tracks['tracks']:
        recommended_tracks.append(track['id'])
    return True


def get_by_song(artist_name, song_name):
    global last_fm_tracks
    try:
        last_fm_tracks = pylast.Track(artist_name, song_name, last_fm_network).get_similar(limit=40)
    except pylast.WSError:
        return False
    return find_tracks_in_spotify()


def get_by_tag(tag_name):
    global last_fm_tracks
    last_fm_tracks = pylast.Tag(name=tag_name, network=last_fm_network).get_top_tracks(cacheable=False, limit=120)
    if last_fm_tracks is None:
        return False
    if len(last_fm_tracks) >= 80:
        last_fm_tracks = last_fm_tracks[20:120]
    return find_tracks_in_spotify()


def get_by_recently_played():
    global artist_tracks
    recently_played_artists = []
    recently_played_tracks = spotify.current_user_recently_played()
    if len(recently_played_tracks['items']) > 0:
        for track in recently_played_tracks['items']:
            artist_id = track['track']['artists'][0]['id']
            if artist_id not in recently_played_artists:
                recently_played_artists.append(artist_id)
                get_albums(artist_id)
                select_songs(2)
                artist_tracks.clear()
        return True
    else:
        return False


def get_by_new_releases():
    global artist_tracks
    new_releases = spotify.new_releases(country="TR")
    if new_releases['albums']['total'] > 0:
        for album in new_releases['albums']['items']:
            get_tracks(album['id'])
            select_songs(2)
            artist_tracks.clear()
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
        get_by_related_artists(artist_name=artist_names[randon_number], song_number=1)
        if len(artist_names) > 5:
            del artist_names[randon_number]
    return True


def get_by_tag_artists(tag_name):
    global last_fm_tracks
    not_empty = False
    artists = pylast.Tag(name=tag_name, network=last_fm_network).get_top_artists(cacheable=False, limit=30)
    if not artists:
        return False
    for artist in artists:
        last_fm_tracks = pylast.Artist(name=artist.item, network=last_fm_network).get_top_tracks(cacheable=False,
                                                                                                 limit=3)
        result = find_tracks_in_spotify()
        if result:
            not_empty = True
    if not_empty:
        return True
    return False


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


def add_to_playlist(playlist_name):
    global playlist_id
    if len(recommended_tracks) > 0:
        get_user_playlists()
        playlist_id = get_playlist_id(playlist_name)
        # playlist_id = playlist_name
        for i in range(0, len(recommended_tracks), 100):
            spotify.user_playlist_add_tracks("", playlist_id, recommended_tracks[:100])


def overwrite_playlist(playlist_name):
    global playlist_id
    if len(recommended_tracks) > 0:
        get_user_playlists()
        playlist_id = get_playlist_id(playlist_name)
        # playlist_id = playlist_name
        spotify.user_playlist_replace_tracks("", playlist_id, recommended_tracks[:100])
        for i in range(100, len(recommended_tracks), 100):
            spotify.user_playlist_add_tracks("", playlist_id, recommended_tracks[i:i + 100])


def delete_tracks():
    global recommended_tracks
    recommended_tracks.clear()


def play():
    playlist_uri = spotify.user_playlist(user=spotify_username, playlist_id=playlist_id)
    devices = spotify.devices()
    if len(devices['devices']) > 0:
        spotify.start_playback(context_uri=playlist_uri['uri'])
        spotify.shuffle(state=True)
        return True
    return False


dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

client_id = os.environ.get("client_id")
client_secret = os.environ.get("client_secret")
redirect_uri = os.environ.get("redirect_uri")
spotify_username = os.environ.get("spotify_username")
scope = os.environ.get("scope")

try:
    token = util.prompt_for_user_token(spotify_username, scope, client_id, client_secret, redirect_uri)
except(AttributeError, JSONDecodeError):
    os.remove(f".cache-{spotify_username}")
    token = util.prompt_for_user_token(spotify_username, scope, client_id, client_secret, redirect_uri)
spotify = spotipy.Spotify(auth=token)

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
last_fm_username = os.environ.get("last_fm_username")
password_hash = pylast.md5(os.environ.get("password_hash"))
last_fm_network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET,
                                       username=last_fm_username, password_hash=password_hash)

connection = sqlite3.connect('spotify.sqlite3')
c = connection.cursor()

artist_tracks = []
recommended_tracks = []
last_fm_tracks = []
playlists = []
playlist_id = ""

# c.execute("SELECT * FROM track ")
# result = c.fetchall()
# connection.close()

# print(json.dumps(artist, sort_keys=True, indent=4))
# quit()
