from spotify import *

get_by_artist("Don Mclean)
get_by_related_artists("Mumford & Sons")
get_by_genres(["acoustic", "piano", "rainy-day"])
get_by_song("Kodaline", "Way Back When")
get_by_top_artists("long_term")
get_by_tag("melancholic")
get_tag_artist("chillout")  # TODO make it useful
get_by_recently_played()
get_by_new_releases()

add_to_playlist("recommended songs")
override_playlist("recommended songs")  # TODO make playlist settings
