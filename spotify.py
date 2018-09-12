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


def get_by_artist(artist_name):
    global artist_tracks
    artist = spotify.search(artist_name, 1, 0, "artist")
    if artist['artists']['total'] > 0:
        get_albums(artist['artists']['items'][0]['id'])
        select_songs(30)
        artist_tracks.clear()
    else:
        return False


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
        last_fm_tracks = pylast.Track(artist_name, song_name, last_fm_network).get_similar(limit=40)
    except pylast.WSError:
        return False
    find_tracks_in_spotify()


def get_by_tag(tag_name):
    global last_fm_tracks
    last_fm_tracks = pylast.Tag(name=tag_name, network=last_fm_network).get_top_tracks(cacheable=False, limit=120)
    if last_fm_tracks is None:
        return False
    if len(last_fm_tracks) >= 80:
        last_fm_tracks = last_fm_tracks[20:120]
    find_tracks_in_spotify()


def get_by_recently_played():
    global artist_tracks
    recently_played_artists = []
    recently_played_tracks = spotify.current_user_recently_played()
    for track in recently_played_tracks['items']:
        artist_id = track['track']['artists'][0]['id']
        if artist_id not in recently_played_artists:
            recently_played_artists.append(artist_id)
            get_albums(artist_id)
            select_songs(2)
            artist_tracks.clear()


def get_by_new_releases():
    global artist_tracks
    new_releases = spotify.new_releases(country="TR")
    for album in new_releases['albums']['items']:
        get_tracks(album['id'])
        select_songs(2)
        artist_tracks.clear()


def get_tag_artist(tag_name):
    artists = pylast.Tag(name=tag_name, network=last_fm_network).get_top_artists(cacheable=False, limit=120)
    for artist in artists:
        print(artist.item)


def get_user_playlists():
    global playlists
    user_playlists = spotify.current_user_playlists(limit=50, offset=0)
    for playlist in user_playlists['items']:
        if playlist['owner']['id'] == spotify_username:
            playlists.append({'id': playlist['id'], 'name': playlist['name']})


def get_playlist_id(playlist_name):
    global playlists
    for playlist in playlists:
        if playlist_name == playlist['name']:
            return playlist['id']
    playlist = spotify.user_playlist_create(spotify_username, playlist_name, public=False)
    return playlist['id']


def add_to_playlist(playlist_name):
    get_user_playlists()
    playlist_id = get_playlist_id(playlist_name)
    # playlist_id = playlist_name
    for i in range(0, len(recommended_tracks), 100):
        spotify.user_playlist_replace_tracks("", playlist_id, recommended_tracks[:100])


def override_playlist(playlist_name):
    get_user_playlists()
    playlist_id = get_playlist_id(playlist_name)
    # playlist_id = playlist_name
    spotify.user_playlist_replace_tracks("", playlist_id, recommended_tracks[:100])
    for i in range(100, len(recommended_tracks), 100):
        spotify.user_playlist_add_tracks("", playlist_id, recommended_tracks[i:i + 100])


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

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
last_fm_username = os.environ.get("last_fm_username")
password_hash = pylast.md5(os.environ.get("password_hash"))
last_fm_network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET,
                                       username=last_fm_username, password_hash=password_hash)

artist_tracks = []
recommended_tracks = []
last_fm_tracks = []
playlists = []
# print(json.dumps(artist, sort_keys=True, indent=4))
# quit()
