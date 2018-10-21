from spotify import *

while True:
    print("\n0 - Recommend by Artist")
    print("1 - Recommend by Related Artists")
    print("2 - Recommend by Top Played Artists")
    print("3 - Recommend by Recently Played Artists")
    print("4 - Recommend by Song")
    print("5 - Recommend by Genre")
    print("6 - Recommend by Tag")
    print("7 - Recommend by New Releases")
    print("8 - Recommend by Playlist")
    print("9 - Recommend by Tag Artists")
    print("10 - Exit \n")
    choice = input("Your Choice: ")
    if choice == "0":
        artist = input("\nType artist name: ")
        result = get_by_artist(artist)
        if not result:
            print("\n\nArtist not found. Please make another choice.\n\n")
            continue
    elif choice == "1":
        artist = input("\nType artist name: ")
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
        song = input("\nType song name: ")
        result = get_by_song(artist, song)
        if not result:
            print("\n\nSimilar songs not found. Please make another choice.\n\n")
            continue
    elif choice == "5":
        genres = input("\nType genres: ")
        result = get_by_genres(genres.split())
        if not result:
            print("\n\nGenres not found. Please make another choice.\n\nYou can find all available genres here: \n\n")
            genres = get_all_genres()
            for i in range(0, len(genres), 6):
                print(genres[i], "", genres[i + 1], "", genres[i + 2], "",
                      genres[i + 3], "", genres[i + 4], "", genres[i + 5])
            continue
    elif choice == "6":
        tag = input("\nType tag: ")
        result = get_by_tag(tag)
        if not result:
            print("\n\nTag not found. Please make another choice.\n\n")
            continue
    elif choice == "7":
        result = get_by_new_releases()
        if not result:
            print("\n\nNew releases not found. Please make another choice.\n\n")
            continue
    elif choice == "8":
        name = input("\nType playlist name: ")
        result = get_by_playlist(name)
        if not result:
            print("\n\nPlaylist not found or it's empty. Please make another choice.\n\n")
            continue
    elif choice == "9":
        tag = input("\nType tag: ")
        result = get_by_tag_artists(tag)
        if not result:
            print("\n\nRelated artists not found. Please make another choice.\n\n")
            continue
    elif choice == "10":
        break
    else:
        print("\nWrong input. Please make another choice.\n")
        continue
    while True:
        print("\n0 - Add tracks to playlist")
        print("1 - Overwrite playlist")
        print("2 - Do Nothing\n")
        choice = input("Your choice: ")
        if choice == "0":
            name = input("\nType playlist name: ")
            add_to_playlist(name)
            print("\nPress 1 to Start Playing\n")
            play_choice = input("")
            if play_choice == "1":
                play()
            break
        elif choice == "1":
            name = input("\nType playlist name: ")
            overwrite_playlist(name)
            print("\nPress 1 to Start Playing\n")
            play_choice = input("")
            if play_choice == "1":
                result = play()
                if not result:
                    print("\n\nDevices not found.\n\n")
            break
        elif choice == "2":
            break
        print("\nWrong input. Please make another choice.\n")
    delete_tracks()
