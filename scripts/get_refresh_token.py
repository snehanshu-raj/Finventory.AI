"""One-time script to get a Google OAuth refresh token.

Run this once, copy the refresh token into your .env file, and you're done forever.

Usage:
    python scripts/get_refresh_token.py
"""

import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import httpx
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:9999/callback"
SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
TOKEN_URL = "https://oauth2.googleapis.com/token"

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = parse_qs(urlparse(self.path).query)
        auth_code = query.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Done! You can close this tab.</h1><p>Go back to your terminal.</p>")

    def log_message(self, *args):
        pass  # suppress logs


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be in .env")
        return

    # Open browser for consent
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code"
        f"&scope={SCOPE}&access_type=offline&prompt=consent"
    )
    print(f"\nOpening browser for Google sign-in...")
    print(f"If the browser doesn't open, manually visit:\n{auth_url}\n")
    webbrowser.open(auth_url)

    # Wait for callback
    server = HTTPServer(("localhost", 9999), CallbackHandler)
    print("Waiting for Google callback...")
    server.handle_request()

    if not auth_code:
        print("ERROR: No auth code received")
        return

    # Exchange code for tokens
    print("Exchanging auth code for tokens...")
    resp = httpx.post(TOKEN_URL, data={
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    })

    if resp.status_code != 200:
        print(f"ERROR: Token exchange failed: {resp.text}")
        return

    tokens = resp.json()
    refresh_token = tokens.get("refresh_token")

    if not refresh_token:
        print("ERROR: No refresh token returned. Try adding prompt=consent to the URL.")
        return

    print(f"\n{'='*60}")
    print(f"SUCCESS! Add this to your .env file:")
    print(f"{'='*60}")
    print(f"\nGOOGLE_REFRESH_TOKEN={refresh_token}")
    print(f"\n{'='*60}")


if __name__ == "__main__":
    main()
