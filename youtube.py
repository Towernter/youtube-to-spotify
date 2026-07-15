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
        # Check if the title contains a clear delimiter (" - ")
        if "-" in title:
            parts = title.split("-")
            if len(parts) == 2:
                # Try both formats and see which one works better
                # Format 1: Assume "Artist - Song Name"
                artist_first = parts[0].strip()
                song_first = parts[1].strip()

                # Format 2: Assume "Song Name - Artist"
                song_second = parts[0].strip()
                artist_second = parts[1].strip()

                # Return both possibilities
                return (song_first, artist_first), (song_second, artist_second)

        # If no clear delimiter, return the title as the song name
        return (title, ""), (title, "")

    # Patterns whose bracket content is purely noise (no alternative title inside)
    _NOISE_BRACKET = re.compile(
        r'^(?:official|music|video|lyrics?|lyric|visualizer|audio|hq|hd|4k|1080p|'
        r'live|remix|version|edit|clip|cover|feat|ft|featuring|prod|by|mv|ep)\b',
        re.IGNORECASE
    )

    def extract_bracket_alternatives(self, text):
        """Return non-noise text found inside (), [], {} as potential alternative titles."""
        matches = re.findall(r'[\(\[\{]([^\)\]\}]+)[\)\]\}]', text)
        results = []
        for m in matches:
            m = m.strip()
            if not m:
                continue
            if self._NOISE_BRACKET.match(m):
                continue
            # Require at least one substantive word (>3 chars, not a noise word)
            substantive = [w for w in m.split() if len(w) > 3 and not self._NOISE_BRACKET.match(w)]
            if substantive:
                results.append(m)
        return results

    def clean_title(self, title):
        # Remove anything in brackets (e.g., (Official Video), [Lyrics], etc.)
        title = re.sub(r'\(.*?\)|\[.*?\]|\{.*?\}|#\S+', '', title)

        # Remove common unwanted phrases (case-insensitive)
        unwanted_phrases = [
            "official music video", "official video", "lyrics", "lyric video", "album",
            "visualizer", "live", "ft.", "ft", "feat.", "featuring", "prod.", "remix",
            "version", "starring", "by", "audio", "video", "hq", "hd", "4k", "1080p",
            "lyric", "clip", "performance", "cover", "original", "extended", "edit",
            "radio edit", "acoustic", "live session", "live performance", "live at",
            "with lyrics", "with subtitles", "full song", "full album", "full video",
            "official audio", "official hd", "official", "official clip", "official lyric video",
            "official remix", "official live", "official performance", "official cover",
            "official extended", "official edit", "official radio edit", "official acoustic",
            "official live session", "official live performance", "official live at",
            "official with lyrics", "official with subtitles", "official full song",
            "official full album", "official full video", "official hq", "official 4k",
            "official 1080p", "official lyric", "official clip", "official performance",
            "official cover", "official original", "official extended", "official edit",
            "official radio edit", "official acoustic", "official live session",
            "official live performance", "official live at", "official with lyrics",
            "official with subtitles", "official full song", "official full album",
            "official full video", "official hq", "official 4k", "official 1080p"
        ]
        for phrase in unwanted_phrases:
            title = re.sub(fr'(?i)\b{re.escape(phrase)}\b', '', title)

        # Remove special characters and symbols
        title = re.sub(r"[^\w\s&\-'']", '', title)  # Keep alphanumeric, spaces, &, and -

        # Remove hashtags and mentions
        # title = re.sub(r'#\S+', '', title)  # Remove hashtags
        title = re.sub(r'@\S+', '', title)  # Remove mentions

        # Remove extra spaces and trim
        title = re.sub(r'\s+', ' ', title).strip()

        return title
    
