import os
import spotipy
import spotipy.util as util
import json
from json.decoder import JSONDecodeError
import random
import pylast


def get_tracks(i):
    global allTracks
    i = spotify.album_tracks(i)
    for j in i['items']:
        allTracks.append(j['id'])


def get_albums(i):
    i = spotify.artist_albums(artist_id=i, album_type="album", limit=5)
    for j in i['items']:
        get_tracks(j['id'])


def get_related_artists(i):
    global allTracks, recommendTracks
    i = spotify.artist_related_artists(i)
    for j in i['artists']:
        get_albums(j['id'])
        recommendTracks.append(random.choice(allTracks))
        allTracks.clear()


username = "oguzcancelik"
scope = 'user-read-private ' \
        'user-read-playback-state ' \
        'user-modify-playback-state ' \
        'playlist-modify-public ' \
        'playlist-modify-private ' \
        'user-read-recently-played ' \
        'user-top-read'

try:
    token = util.prompt_for_user_token(username, scope)
except(AttributeError, JSONDecodeError):
    os.remove(f".cache-{username}")
    token = util.prompt_for_user_token(username, scope)

API_KEY = "***"
API_SECRET = "***"
usernameL = "oguzcancelk"
password_hash = pylast.md5("***")

spotify = spotipy.Spotify(auth=token)
lastfm = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET, username=usernameL, password_hash=password_hash)
artists = []
allTracks = []
recommendTracks = []

print("Welcome " + username)
while True:
    print()
    print("0 - Recommend by Artist")
    print("1 - Recommend by Top Played Artists")
    print("2 - Recommend by Song")
    print("3 - Exit")
    print()
    choice = input("Your Choice: ")
    if choice == "0":
        artist = input("\nType artist name: ")
        artist = spotify.search(artist, 1, 0, "artist")
        if artist['artists']['total'] == 0:
            print("\nArtist not found\n")
            continue
        artists = artist['artists']
    elif choice == "1":
        while True:
            print()
            print("0 - Short Term")
            print("1 - Medium Term")
            print("2 - Long Term")
            term = input("Choose term: ")
            if term == "0":
                term = "short_term"
            elif term == "1":
                term = "medium_term"
            elif term == "2":
                term = "long_term"
            else:
                print("Input must be one of the followings.")
                continue
            artists = spotify.current_user_top_artists(limit=5, offset=0, time_range=term)
            break
    elif choice == "2":
        artist = input("\nType artist name: ")
        song = input("\nType song name: ")
        similarSongs = pylast.Track(artist, song, lastfm).get_similar(limit=20)
        for i in similarSongs:
            allTracks.append(i.item)
        for i in allTracks:
            j = spotify.search(str(i.get_name()) + " " + str(i.get_artist()), 1, 0, "track")
            if j['tracks']['total'] == 0:
                continue
            j = j['tracks']['items'][0]['id']
            recommendTracks.append(str(j))
    elif choice == "3":
        break
    else:
        print("Input must be one of the followings.")
        continue
    print("\nSearching for the songs..\n")
    if len(artists) != 0:
        for i in artists['items']:
            get_related_artists(i['id'])
    spotify.user_playlist_add_tracks("oguzcancelik", "44uE9HX0RaoCHjXErRWZJD", recommendTracks, position=None)
    print(str(len(recommendTracks)) + " recommendedsongs added to the playlist.\n")
    recommendTracks.clear()
    artists.clear()

# print(json.dumps(result, sort_keys=True, indent=4))
