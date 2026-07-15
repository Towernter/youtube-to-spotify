# script.py
from spotify import SpotifyAPI
from youtube import YouTubeAPI
from dotenv import load_dotenv
import os

def main():
    load_dotenv()

    # Load credentials from .env
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    refresh_token = os.getenv('REFRESH_TOKEN')
    spotify_playlist_id = os.getenv('SPOTIFY_PLAYLIST_ID')
    api_key = os.getenv('API_KEY')
    youtube_playlist_id = os.getenv('YOUTUBE_PLAYLIST_ID')

    # Make sure nothing is missing
    required = {
        'CLIENT_ID': client_id,
        'CLIENT_SECRET': client_secret,
        'REFRESH_TOKEN': refresh_token,
        'SPOTIFY_PLAYLIST_ID': spotify_playlist_id,
        'API_KEY': api_key,
        'YOUTUBE_PLAYLIST_ID': youtube_playlist_id,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    # Connect to both APIs
    spotify = SpotifyAPI(client_id, client_secret, refresh_token)
    youtube = YouTubeAPI(api_key)

    sync_playlist(spotify_playlist_id, youtube_playlist_id, spotify, youtube)


def sync_playlist(spotify_playlist_id, youtube_playlist_id, spotify, youtube, remove=True):
    print("Fetching YouTube playlist...")
    youtube_videos = youtube.get_playlist_items(youtube_playlist_id)
    print(f"Found {len(youtube_videos)} videos on YouTube.\n")

    found_tracks = []
    not_found = []

    for i, (title, url) in enumerate(youtube_videos, start=1):
        # Skip deleted or private videos
        if any(word in title.lower() for word in ["deleted", "private"]):
            print(f"{i}. Skipped (Deleted/Private): {title}")
            continue

        # YouTube titles come in two flavours:
        #   "Artist - Song"  or  "Song - Artist"
        # We try both and take whichever finds a match first.
        (song_a, artist_a), (song_b, artist_b) = youtube.extract_song_and_artist(title)

        query_a = f"{youtube.clean_title(song_a)} {youtube.clean_title(artist_a)}".strip()
        query_b = f"{youtube.clean_title(song_b)} {youtube.clean_title(artist_b)}".strip()

        print(f"Searching: {query_a}")

        result = spotify.search_song(query_a) or spotify.search_song(query_b)

        # Last resort: try any alternative title hidden in brackets
        # e.g. "Stayin' Alive (From Saturday Night Fever)" → try "Saturday Night Fever" too
        if not result:
            for alt in (youtube.extract_bracket_alternatives(song_a) +
                        youtube.extract_bracket_alternatives(song_b)):
                alt_query = f"{youtube.clean_title(alt)} {youtube.clean_title(artist_a)}".strip()
                result = spotify.search_song(alt_query)
                if result:
                    break

        if result:
            found_tracks.append(result['uri'])
            print(f"{i}. Found: {result['song_name']} by {result['artists']}")
        else:
            not_found.append(title)
            print(f"{i}. Not found: {title}")

    # --- Add new tracks ---
    spotify_tracks = spotify.get_playlist_tracks(spotify_playlist_id)
    spotify_uris = [t['uri'] for t in spotify_tracks]

    to_add = [uri for uri in found_tracks if uri not in spotify_uris]
    if to_add:
        print(f"\nAdding {len(to_add)} new tracks...")
        spotify.add_tracks_to_playlist(spotify_playlist_id, to_add)

    # --- Remove tracks that are no longer in the YouTube playlist ---
    if remove:
        to_remove = [uri for uri in spotify_uris if uri not in found_tracks]
        if to_remove:
            print(f"Removing {len(to_remove)} tracks...")
            spotify.remove_tracks_from_playlist(spotify_playlist_id, to_remove)

    # --- Reorder Spotify playlist to match YouTube order ---
    print("\nReordering playlist to match YouTube order...")
    if len(youtube_videos) > 100:
        spotify.reorder_playlist_many_tracks(spotify_playlist_id, found_tracks)
    else:
        spotify.reorder_playlist_tracks(spotify_playlist_id, found_tracks)

    # --- Summary ---
    print("\n--- Done ---")
    print(f"YouTube videos:     {len(youtube_videos)}")
    print(f"Found on Spotify:   {len(found_tracks)}")
    print(f"Not found:          {len(not_found)}")
    print(f"Added:              {len(to_add)}")
    if remove:
        print(f"Removed:            {len(to_remove)}")


if __name__ == '__main__':
    main()
