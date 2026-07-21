# get_refresh_token.py
# One-off helper: runs the Spotify Authorization Code flow to mint a new
# refresh token. Opens a browser, you click "Agree", it prints the token.
#
# Prereq: add  http://127.0.0.1:8888/callback  to your app's Redirect URIs
# in the Spotify dashboard first.
import base64
import os
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://127.0.0.1:8888/callback'
SCOPES = 'playlist-modify-public playlist-modify-private playlist-read-private playlist-read-collaborative'

auth_code = {}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        auth_code['code'] = params.get('code', [None])[0]
        auth_code['error'] = params.get('error', [None])[0]
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        msg = 'Authorization received. You can close this tab.' if auth_code.get('code') \
            else f"Authorization failed: {auth_code.get('error')}"
        self.wfile.write(f'<html><body><h3>{msg}</h3></body></html>'.encode())

    def log_message(self, *args):
        pass  # silence the default request logging


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        raise SystemExit('CLIENT_ID / CLIENT_SECRET missing from .env')

    auth_url = 'https://accounts.spotify.com/authorize?' + urllib.parse.urlencode({
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
    })

    print('Opening browser to authorize...')
    print('If it does not open, paste this URL manually:\n' + auth_url + '\n')
    webbrowser.open(auth_url)

    # Wait for the single callback request
    server = HTTPServer(('127.0.0.1', 8888), Handler)
    server.handle_request()

    if not auth_code.get('code'):
        raise SystemExit(f"No auth code received (error: {auth_code.get('error')})")

    # Exchange the code for tokens
    resp = requests.post(
        'https://accounts.spotify.com/api/token',
        headers={
            'Authorization': 'Basic ' + base64.b64encode(
                f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode(),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        data={
            'grant_type': 'authorization_code',
            'code': auth_code['code'],
            'redirect_uri': REDIRECT_URI,
        },
    )
    if not resp.ok:
        raise SystemExit(f'Token exchange failed ({resp.status_code}): {resp.text}')

    refresh_token = resp.json().get('refresh_token')
    print('\n' + '=' * 60)
    print('NEW REFRESH TOKEN:\n')
    print(refresh_token)
    print('=' * 60)
    print('\nUpdate REFRESH_TOKEN with this value in:')
    print('  - .env (both projects)')
    print('  - GitHub Actions secrets (both repos)')


if __name__ == '__main__':
    main()
