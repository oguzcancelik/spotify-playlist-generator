import os
from dotenv import load_dotenv, find_dotenv
import spotipy
import spotipy.util as util
import json
from json.decoder import JSONDecodeError
import random
import pylast


def find_tracks_in_spotify():
    global last_fm_tracks
    for last_fm_track in last_fm_tracks:
        track = spotify.search(last_fm_track.item, 1, 0, "track")
        if track['tracks']['total'] > 0:
            recommended_tracks.append(track['tracks']['items'][0]['id'])


def select_songs(song_number):
    global artist_tracks, recommended_tracks
    for i in range(song_number):
        randon_number = random.randint(0, len(artist_tracks) - 1)
        recommended_tracks.append(artist_tracks[randon_number])
        del artist_tracks[randon_number]


def get_tracks(album_id):
    global artist_tracks
    tracks = spotify.album_tracks(album_id)
    for track in tracks['items']:
        artist_tracks.append(track['id'])


def get_albums(artist_id):
    albums = spotify.artist_albums(artist_id=artist_id, album_type="album", limit=10)
    for album in albums['items']:
        get_tracks(album['id'])


def get_by_related_artists(artist_name):
    global artist_tracks
    artist = spotify.search(artist_name, 1, 0, "artist")
    if artist['artists']['total'] > 0:
        related_artists = spotify.artist_related_artists(artist['artists']['items'][0]['id'])
        if len(related_artists['artists']) > 0:
            related_artists['artists'].append({'id': artist['artists']['items'][0]['id']})
            for related_artist in related_artists['artists']:
                get_albums(related_artist['id'])
                select_songs(4)
                artist_tracks.clear()
        else:
            return False
    else:
        return False


def get_by_artist(artist_name):
    global artist_tracks
    artist = spotify.search(artist_name, 1, 0, "artist")
    if artist['artists']['total'] > 0:
        get_albums(artist['artists']['items'][0]['id'])
        select_songs(30)
        artist_tracks.clear()
    else:
        return False


def get_by_top_artists(term):
    global artist_tracks
    top_artists = spotify.current_user_top_artists(limit=20, offset=0, time_range=term)
    if top_artists['total'] > 0:
        for artist in top_artists['items']:
            get_albums(artist['id'])
            select_songs(5)
            artist_tracks.clear()
    else:
        return False


def get_by_genres(genres):
    global recommended_tracks
    # all_genres = spotify.recommendation_genre_seeds()
    tracks = spotify.recommendations(limit=50, seed_genres=genres, country="TR")
    if len(tracks['tracks']) == 0:
        return False
    for track in tracks['tracks']:
        recommended_tracks.append(track['id'])


def get_by_song(artist_name, song_name):
    global last_fm_tracks
    try:
        last_fm_tracks = pylast.Track(artist_name, song_name, lastfm).get_similar(limit=40)
    except pylast.WSError:
        return False
    find_tracks_in_spotify()


def get_by_tag(tag_name):
    global last_fm_tracks
    last_fm_tracks = pylast.Tag(name=tag_name, network=lastfm).get_top_tracks(cacheable=False, limit=120)
    if last_fm_tracks is None:
        return False
    if len(last_fm_tracks) >= 80:
        last_fm_tracks = last_fm_tracks[20:120]
    find_tracks_in_spotify()


def get_tag_artist(tag_name):
    artists = pylast.Tag(name=tag_name, network=lastfm).get_top_artists(cacheable=False, limit=120)
    for artist in artists:
        print(artist.item)


def add_to_playlist():
    for i in range(0, len(recommended_tracks), 100):
        spotify.user_playlist_add_tracks("oguzcancelik", "44uE9HX0RaoCHjXErRWZJD", recommended_tracks[i:i + 100])


def override_playlist():
    spotify.user_playlist_replace_tracks("oguzcancelik", "44uE9HX0RaoCHjXErRWZJD", recommended_tracks[:100])
    for i in range(100, len(recommended_tracks), 100):
        spotify.user_playlist_add_tracks("oguzcancelik", "44uE9HX0RaoCHjXErRWZJD", recommended_tracks[i:i + 100])


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
        'user-top-read'

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
lastfm = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET, username=last_fm_username,
                              password_hash=password_hash)

artist_tracks = []
recommended_tracks = []
last_fm_tracks = []

# print(json.dumps(artist, sort_keys=True, indent=4))
# quit()
