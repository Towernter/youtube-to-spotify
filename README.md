# YouTube to Spotify

Automatically mirrors a YouTube playlist to Spotify. Every day, on a schedule, without you lifting a finger.

The script fetches all videos from a YouTube playlist, finds each song on Spotify, and keeps your Spotify playlist perfectly in sync — same songs, same order. Songs added to YouTube show up on Spotify. Songs removed disappear. You just listen.

```
--- Done ---
YouTube videos:     150
Found on Spotify:   145
Not found:          5
Added:              12
Removed:            0
```

---

## The Tutorial Series

This repo is the companion code for a six-chapter series published on DEV. Each chapter covers one part of building and deploying this project from scratch, written for beginners — no prior coding experience required.

| # | Chapter | What it covers |
|---|---------|----------------|
| 1 | [Getting Started](https://dev.to/towernter/automate-spotify-apple-and-youtube-music-playlists-f7c) | What we're building, how APIs work, and the four accounts you need |
| 2 | [Setting Up Spotify](https://dev.to/towernter/automate-spotify-and-youtube-playlists-chapter-2-setting-up-spotify-314a) | Creating a Spotify developer app and getting your CLIENT_ID, CLIENT_SECRET, and REFRESH_TOKEN |
| 3 | [Setting Up YouTube](https://dev.to/towernter/automate-spotify-and-youtube-playlists-chapter-3-setting-up-youtube-4nk1) | Enabling the YouTube Data API on Google Cloud and finding your playlist ID |
| 4 | [Writing the Code](https://dev.to/towernter/automate-spotify-and-youtube-playlists-chapter-4-writing-the-code-4b5a) | A plain-English walkthrough of all three Python files and how the sync logic works |
| 5 | [Running It Locally](https://dev.to/towernter/automate-spotify-and-youtube-playlists-chapter-5-running-it-locally-g0f) | Installing Python, setting up a virtual environment, and running the script for the first time |
| 6 | [Deployment](https://dev.to/towernter/automate-spotify-and-youtube-playlists-chapter-6-deployment-4lmh) | Pushing to GitHub and setting up a GitHub Actions workflow that runs daily at midnight UTC |

---

## Project Structure

```
youtube-to-spotify/
├── .github/
│   └── workflows/
│       └── sync.yml        # GitHub Actions — runs daily at midnight UTC
├── spotify.py              # Spotify API client
├── youtube.py              # YouTube API client
├── script.py               # Entry point — runs the sync
├── requirements.txt        # Python dependencies
├── .gitignore
└── .env                    # Your credentials (never committed)
```

---

## Setup

### 1. Clone the repo and create a virtual environment

```bash
git clone https://github.com/Towernter/youtube-to-spotify.git
cd youtube-to-spotify
python -m venv venv
```

Activate it:

```bash
# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file

```
CLIENT_ID=your_spotify_client_id
CLIENT_SECRET=your_spotify_client_secret
REFRESH_TOKEN=your_spotify_refresh_token
SPOTIFY_PLAYLIST_ID=your_spotify_playlist_id
API_KEY=your_youtube_api_key
YOUTUBE_PLAYLIST_ID=PLGBuKfnErZlAkaUUy57-mR97f8SBgMNHh
```

Chapters 2 and 3 of the series walk through getting each of these values.

### 4. Run

```bash
python script.py
```

---

## Automated Deployment

The included GitHub Actions workflow (`.github/workflows/sync.yml`) runs the script every day at midnight UTC. To use it:

1. Push this repo to GitHub
2. Go to **Settings → Secrets and variables → Actions** and add all six credentials as repository secrets
3. The workflow runs automatically on schedule, or trigger it manually from the **Actions** tab

---

## The YouTube Playlist

The series uses the [70s Music Hits](https://www.youtube.com/playlist?list=PLGBuKfnErZlAkaUUy57-mR97f8SBgMNHh) playlist by Redlist Decades as the source. To sync a different playlist, update `YOUTUBE_PLAYLIST_ID` in your `.env` file (or GitHub Secrets) and re-run.
