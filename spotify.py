# spotify.py
import requests
import base64
import re

class SpotifyAPI:
    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.token = self.refresh_access_token()

    def refresh_access_token(self):
        token_url = 'https://accounts.spotify.com/api/token'
        headers = {
            'Authorization': 'Basic ' + base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode(),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()['access_token']

    def fetch_web_api(self, endpoint, method='GET', body=None):
        url = f'https://api.spotify.com/v1/{endpoint}'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        response = requests.request(method, url, json=body, headers=headers)
        if response.status_code == 401:
            print('Refreshing access token...')
            self.token = self.refresh_access_token()
            headers['Authorization'] = f'Bearer {self.token}'
            response = requests.request(method, url, json=body, headers=headers)
        response.raise_for_status()

        if response.status_code == 200 and not response.content.strip():
            return None

        return response.json()

    def get_playlist_tracks(self, playlist_id):
        fields = 'items(track(id,uri,name,artists(name),album(release_date),popularity),added_at)'
        endpoint = f'playlists/{playlist_id}/tracks?fields={fields}'
        data = self.fetch_web_api(endpoint)
        return [
            {
                'id': item['track']['id'],
                'uri': item['track']['uri'],
                'song_name': item['track']['name'],
                'artists': ', '.join(artist['name'] for artist in item['track']['artists']),
                'date_added': item['added_at'],
                'release_date': item['track']['album']['release_date'],
                'popularity': item['track']['popularity']
            }
            for item in data.get('items', [])
        ]

    def _make_track_result(self, track):
        return {
            'id': track['id'],
            'uri': track['uri'],
            'song_name': track['name'],
            'artists': ', '.join(a['name'] for a in track['artists']),
            'album': track['album']['name'],
            'release_date': track['album']['release_date'],
            'popularity': track['popularity'],
        }

    def search_song(self, query, limit=10):
        endpoint = f'search?q={query}&type=track&limit={limit}'
        data = self.fetch_web_api(endpoint)
        tracks = data.get('tracks', {}).get('items', [])
        if not tracks:
            return None

        # Pass 1: full query is a substring of track name or combined artists
        for track in tracks:
            track_artists = ', '.join(a['name'] for a in track['artists'])
            if query.lower() in track['name'].lower() or query.lower() in track_artists.lower():
                return self._make_track_result(track)

        stop_words = {'the', 'a', 'an', 'and', 'or', 'by', 'ft', 'feat', 'with', 'of', 'in', 'on'}
        query_words = {w.lower() for w in query.split() if len(w) > 2 and w.lower() not in stop_words}

        # Pass 2: artist-name matching
        for track in tracks:
            title_words = set(track['name'].lower().split())
            matched_artists = sum(
                1 for artist in track['artists']
                if query_words & {w.lower() for w in re.split(r'\W+', artist['name']) if len(w) > 2}
            )
            if matched_artists >= 2:
                return self._make_track_result(track)
            if matched_artists == 1:
                if query_words & title_words:
                    return self._make_track_result(track)
                if any(
                    len(qw) >= 4 and len(tw) >= 4 and (qw in tw or tw in qw)
                    for qw in query_words for tw in title_words
                ):
                    return self._make_track_result(track)

        # Pass 3: two or more query words appear in the track title
        for track in tracks:
            if len(query_words & set(track['name'].lower().split())) >= 2:
                return self._make_track_result(track)

        return None

    def add_tracks_to_playlist(self, playlist_id, track_uris):
        endpoint = f'playlists/{playlist_id}/tracks'
        batch_size = 100
        existing_uris = {track['uri'] for track in self.get_playlist_tracks(playlist_id)}
        unique_uris = [uri for uri in track_uris if uri not in existing_uris]
        total = len(unique_uris)

        for i in range(0, total, batch_size):
            batch = unique_uris[i:i + batch_size]
            response = self.fetch_web_api(endpoint, method='POST', body={'uris': batch})
            if response.get('snapshot_id'):
                print(f"Added {len(batch)} tracks - {i + len(batch)}/{total} complete.")
            else:
                print(f"Failed to add batch starting at {i}.")

        print(f"Finished adding all {total} tracks.")

    def remove_tracks_from_playlist(self, playlist_id, track_uris):
        endpoint = f'playlists/{playlist_id}/tracks'
        batch_size = 100
        for i in range(0, len(track_uris), batch_size):
            batch = [{'uri': uri} for uri in track_uris[i:i + batch_size]]
            self.fetch_web_api(endpoint, method='DELETE', body={'tracks': batch})
            print(f"Removed {len(batch)} tracks from playlist.")

    def reorder_playlist_tracks(self, playlist_id, track_uris):
        endpoint = f'playlists/{playlist_id}/tracks'
        body = {'uris': track_uris[:100]}
        self.fetch_web_api(endpoint, method='PUT', body=body)

        current_tracks = self.get_playlist_tracks(playlist_id)
        current_uris = [t['uri'] for t in current_tracks]

        for i, uri in enumerate(track_uris):
            current_index = current_uris.index(uri)
            if current_index != i:
                body = {'range_start': current_index, 'insert_before': i}
                self.fetch_web_api(f'playlists/{playlist_id}/tracks', method='PUT', body=body)
                current_uris.insert(i, current_uris.pop(current_index))

        print(f"Finished reordering {len(track_uris)} tracks.")

    def reorder_playlist_many_tracks(self, playlist_id, track_uris):
        current_tracks = self.get_playlist_tracks(playlist_id)
        current_uris = [t['uri'] for t in current_tracks]

        uri_to_index = {uri: idx for idx, uri in enumerate(current_uris)}
        final_order = [uri for uri in track_uris if uri in uri_to_index]

        for i, uri in enumerate(final_order):
            current_index = uri_to_index[uri]
            if current_index != i:
                body = {'range_start': current_index, 'insert_before': i}
                self.fetch_web_api(f'playlists/{playlist_id}/tracks', method='PUT', body=body)
                moved_uri = final_order[current_index]
                uri_to_index[moved_uri] = i
                for u in final_order[i:current_index]:
                    uri_to_index[u] += 1

        print(f"Finished reordering {len(final_order)} tracks.")
