from spotify import *

while True:
    print()
    print("0 - Recommend by Artist")
    print("1 - Recommend by Related Artists")
    print("2 - Recommend by Top Played Artists")
    print("3 - Recommend by Recently Played Artists")
    print("4 - Recommend by Song")
    print("5 - Recommend by Genre")
    print("6 - Recommend by Tag")
    print("7 - Recommend by New Releases")
    print("8 - Recommend by Playlist")
    print("9 - Exit")
    print()
    choice = input("Your Choice: ")
    if choice == "0":
        artist = input("\nType artist name: ")
        get_by_artist(artist)
    elif choice == "1":
        artist = input("\nType artist name: ")
        get_by_related_artists(artist)
    elif choice == "2":
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
                print("Input must be one of the followings:")
                continue
            get_by_top_artists(term)
            break
    elif choice == "3":
        get_by_recently_played()
    elif choice == "4":
        artist = input("\nType artist name: ")
        song = input("\nType song name: ")
        get_by_song(artist, song)
    elif choice == "5":
        genres = input("\nType genres: ")
        get_by_genres(genres.split())
    elif choice == "6":
        tag = input("\nType tag: ")
        get_by_tag(tag)
    elif choice == "7":
        get_by_new_releases()
    elif choice == "8":
        name = input("\nType playlist name: ")
        get_by_playlist(name)
    elif choice == "9":
        break
    else:
        continue
    name = input("\nType playlist name: ")
    while True:
        print()
        print("\n0 - Add tracks to playlist")
        print("1 - Overwrite playlist")
        print("2 - Do Nothing")
        choice = input("Your choice: ")
        if choice == "0":
            add_to_playlist(name)
            break
        elif choice == "1":
            overwrite_playlist(name)
            break
        elif choice == "2":
            break
        print("Input must be one of the followings: ")
    delete_tracks()
