# youtube.py
from googleapiclient.discovery import build
import re

class YouTubeAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def get_playlist_items(self, playlist_id):
        request = self.youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50
        )

        videos = []
        while request:
            response = request.execute()
            for item in response['items']:
                title = item['snippet']['title']
                video_id = item['snippet']['resourceId']['videoId']
                videos.append((title, f"https://www.youtube.com/watch?v={video_id}"))
            request = self.youtube.playlistItems().list_next(request, response)
        return videos

    def extract_song_and_artist(self, title):
        if "-" in title:
            parts = title.split("-")
            if len(parts) == 2:
                artist_first = parts[0].strip()
                song_first = parts[1].strip()
                song_second = parts[0].strip()
                artist_second = parts[1].strip()
                return (song_first, artist_first), (song_second, artist_second)

        return (title, ""), (title, "")

    _NOISE_BRACKET = re.compile(
        r'^(?:official|music|video|lyrics?|lyric|visualizer|audio|hq|hd|4k|1080p|'
        r'live|remix|version|edit|clip|cover|feat|ft|featuring|prod|by|mv|ep)\b',
        re.IGNORECASE
    )

    def extract_bracket_alternatives(self, text):
        matches = re.findall(r'[\(\[\{]([^\)\]\}]+)[\)\]\}]', text)
        results = []
        for m in matches:
            m = m.strip()
            if not m:
                continue
            if self._NOISE_BRACKET.match(m):
                continue
            substantive = [w for w in m.split() if len(w) > 3 and not self._NOISE_BRACKET.match(w)]
            if substantive:
                results.append(m)
        return results

    def clean_title(self, title):
        title = re.sub(r'\(.*?\)|\[.*?\]|\{.*?\}|#\S+', '', title)

        unwanted_phrases = [
            "official music video", "official video", "lyrics", "lyric video", "album",
            "visualizer", "live", "ft.", "ft", "feat.", "featuring", "prod.", "remix",
            "version", "audio", "video", "hq", "hd", "4k", "1080p", "lyric", "clip",
            "performance", "cover", "original", "extended", "edit", "radio edit",
            "acoustic", "live session", "live performance", "official", "official audio",
            "official clip", "official hd", "official 4k", "official 1080p"
        ]
        for phrase in unwanted_phrases:
            title = re.sub(fr'(?i)\b{re.escape(phrase)}\b', '', title)

        title = re.sub(r"[^\w\s&\-'']", '', title)
        title = re.sub(r'@\S+', '', title)
        title = re.sub(r'\s+', ' ', title).strip()

        return title
