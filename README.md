# spotify playlist generator

- It's a command-line program for generating platlists based on user choice.

- Add your spotify username, client_id and client_secret to the .env file and start using.

- Database is empty in the first place so it may run a little slow. Start searching for your favorite artists and they'll be automatically saved to the database and program will run faster and faster.

- Type **python main.py** and make your choice.
```sh
 $  python main.py
    Generate by:
         0 - Artist
         1 - Related Artists
         2 - Top Played Artists
         3 - Recently Played Artists
         4 - Genre
         5 - New Releases
         6 - Playlist
         7 - Artist Genre
         8 - Year
         9 - Live Tracks
         10 - Acoustic Tracks
         11 - Random Tracks
         12 - Exit

    Your Choice:
```
- Each choice generates a different kind of playlist.

| Choice | Playlist Description | Input Example | Song Limit
| ------ | ------ | ------ | ------ |
| 0 - Artist | tracks of entered artist | The Smiths| 30 |
| 1 - Related Artists | tracks of entered artist and him/her related artists | Brandon Flowers| 105 |
| 2 - Top Played Artists | tracks of most played artists of the user | | 100 |
| 3 - Recently Played Artists | tracks of recently played artists of the user | | 100 |
| 4 - Genre | popular tracks of entered genres | british acoustic | 50 |
| 5 - New Releases | tracks from recently released albums | | 50 |
| 6 - Playlist | tracks of artists of given playlist | sleep |
| 7 - Artist Genre | tracks of artists who share the same genre with given artist | Radiohead | 50 |
| 8 - Year | tracks released in given year | 2007 | 50 |
| 9 - Live Tracks | live tracks | | 50 |
| 10 - Acoustic Tracks | acoustic tracks | |50 |
| 11 - Random Tracks | random tracks | | 50 |

- After making a choice, asks to the user to add tracks to a playlist.
```sh
 $  python main.py
    Generate by:
         0 - Artist
         1 - Related Artists
         2 - Top Played Artists
         3 - Recently Played Artists
         4 - Genre
         5 - New Releases
         6 - Playlist
         7 - Artist Genre
         8 - Year
         9 - Live Tracks
         10 - Acoustic Tracks
         11 - Random Tracks
         12 - Exit

    Your Choice: 1

    Type artist name: Brandon Flowers

    0 - Add tracks to playlist
    1 - Overwrite playlist
    2 - Do Nothing

    Your choice: 0

    Type playlist name: brandon
```

| Choice | Description |
| ------ | ------ |
| 0 - Add tracks to playlist | adds tracks to given playlist |
| 1 - Overwrite playlist | deletes all tracks in given playlist and adds new tracks |
| 2 - Do Nothing | skips without any operation |
