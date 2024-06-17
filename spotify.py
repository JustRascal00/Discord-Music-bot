import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

def convert_spotify_url(url):
    if "track" in url:
        track_id = url.split("/")[-1].split("?")[0]
        track = sp.track(track_id)
        query = f"{track['name']} {track['artists'][0]['name']}"
        return query

    elif "playlist" in url:
        playlist_id = url.split("/")[-1].split("?")[0]
        playlist = sp.playlist_tracks(playlist_id)
        queries = [f"{item['track']['name']} {item['track']['artists'][0]['name']}" for item in playlist['items']]
        return queries

    elif "album" in url:
        album_id = url.split("/")[-1].split("?")[0]
        album = sp.album_tracks(album_id)
        queries = [f"{item['name']} {item['artists'][0]['name']}" for item in album['items']]
        return queries

    return None
