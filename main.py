from spotify_gate import *


def validate_input(user_input):
    chars = ["%", "\"", "\\", "/", "<", ">", "(", ")", "UNION"]
    for x in chars:
        if x in user_input:
            print("\nInput can't contain '" + x + "'.\n")
            return False
    return True


while True:
    print("""\nGenerate by:
    0 - Artist
    1 - Related Artists
    2 - Top Played Artists
    3 - Recently Played Artists
    4 - Song
    5 - Genre
    6 - New Release
    7 - Playlist
    8 - Artist Genre
    9 - Year
    10 - Live Tracks
    11 - Acoustic Tracks
    12 - Random Tracks
    13 - Artist Recommendations
    14 - Keyword
    E - Exit\n""")
    choice = input("Your Choice: ")
    if choice == "0":
        artist = input("\nType artist name: ")
        if not validate_input(artist):
            continue
        result = get_by_artist(artist)
        if not result:
            print("\n\nArtist not found. Please make another choice.\n\n")
            continue
    elif choice == "1":
        artist = input("\nType artist name: ")
        if not validate_input(artist):
            continue
        result = get_by_related_artists(artist)
        if not result:
            print("\n\nArtist or related artists not found. Please make another choice.\n\n")
            continue
    elif choice == "2":
        while True:
            print("\n0 - Short Term")
            print("1 - Medium Term")
            print("2 - Long Term\n")
            term = input("Choose term: ")
            if not validate_input(term):
                continue
            if term == "0":
                term = "short_term"
            elif term == "1":
                term = "medium_term"
            elif term == "2":
                term = "long_term"
            else:
                print("\nWrong input. Please make another choice.\n")
                continue
            break
        result = get_by_top_artists(term)
        if not result:
            print("\n\nTop artists not found. Please make another choice.\n\n")
            continue
    elif choice == "3":
        result = get_by_recently_played()
        if not result:
            print("\n\nRecently played songs not found. Please make another choice.\n\n")
            continue
    elif choice == "4":
        artist = input("\nType artist name: ")
        if not validate_input(artist):
            continue
        song = input("\nType song name: ")
        result = get_by_song(artist, song)
        if not validate_input(song):
            continue
        if not result:
            print("\n\nTrack or recommendations not found. Please make another choice.\n\n")
            continue
    elif choice == "5":
        genres = input("\nType genres: ")
        if not validate_input(genres):
            continue
        result = get_by_genres(genres.split())
        if not result:
            print("\n\nGenres not found. Please make another choice.\n")
            list_genres = input("Type 1 to see all available genres: ")
            if list_genres == "1":
                print()
                genres = get_all_genres()
                for i in range(0, len(genres), 6):
                    print(genres[i], "|", genres[i + 1], "|", genres[i + 2], "|", genres[i + 3], "|", genres[i + 4],
                          "|", genres[i + 5])
            continue
    elif choice == "6":
        result = get_by_new_releases()
        if not result:
            print("\n\nNew releases not found. Please make another choice.\n\n")
            continue
    elif choice == "7":
        name = input("\nType playlist name: ")
        if not validate_input(name):
            continue
        result = get_by_playlist(name)
        if not result:
            print("\n\nPlaylist not found or it's empty. Please make another choice.\n\n")
            continue
    elif choice == "8":
        artist = input("\nType artist name: ")
        if not validate_input(artist):
            continue
        result = get_by_artist_genre(artist)
        if not result:
            print("\n\nArtist or genres not found. Please make another choice.\n\n")
            continue
    elif choice == "9":
        year = input("\nType year: ")
        if not validate_input(year):
            continue
        result = get_by_year(year)
        if not result:
            print("\n\nSongs not found. Please make another choice.\n\n")
            continue
    elif choice == "10":
        result = get_live_tracks()
        if not result:
            print("\n\nSongs not found. Please make another choice.\n\n")
            continue
    elif choice == "11":
        result = get_acoustic_tracks()
        if not result:
            print("\n\nSongs not found. Please make another choice.\n\n")
            continue
    elif choice == "12":
        result = get_random()
        if not result:
            print("\n\nSongs not found. Please make another choice.\n\n")
            continue
    elif choice == "13":
        artist = input("\nType artist name: ")
        if not validate_input(artist):
            continue
        result = get_by_artist_recommendations(artist)
        if not result:
            print("\n\nArtist or recommendations not found. Please make another choice.\n\n")
            continue
    elif choice == "14":
        keyword = input("\nType keyword: ")
        if not validate_input(keyword):
            continue
        result = get_by_keyword(keyword)
        if not result:
            print("\n\nArtist or recommendations not found. Please make another choice.\n\n")
            continue
    elif choice == "e" or choice == "E":
        break
    else:
        print("\nWrong input. Please make another choice.\n")
        continue

    while True:
        print("\n0 - Add tracks to playlist")
        print("1 - Overwrite playlist")
        print("2 - Do Nothing\n")
        choice = input("Your choice: ")
        if choice == "0" or choice == "1":
            name = input("\nType playlist name: ")
            add_to_playlist(name, bool(int(choice)))
            play_choice = input("\nPress 1 to Start Playing: ")
            if play_choice == "1":
                result = play()
                if not result:
                    print("\n\nDevices not found.\n\n")
            break
        elif choice == "2":
            break
        print("\nWrong input. Please make another choice.\n")
    delete_tracks()
