"""
One-time Google Drive OAuth2 authorization.

Run this script ONCE from your local machine (not inside Docker) to
authorize AstroNova to access Google Drive on behalf of the project owner.

Usage:
    python authorize_gdrive.py

The generated token file (gdrive_token.json) is auto-mounted into Docker
via the .:/app volume.
"""

import json
import os
import sys
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import requests as _rq  # type: ignore

CLIENT_SECRET = os.path.join(os.path.dirname(__file__), "drive_oauth_client.json")
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "gdrive_token.json")

REDIRECT_PORT = 8765
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"

_auth_code = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        params = parse_qs(urlparse(self.path).query)
        _auth_code = params.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Authorization complete. You can close this tab.")

    def log_message(self, *args):
        pass  # silence server logs


def main():
    if not os.path.exists(CLIENT_SECRET):
        sys.exit(f"Client secret file not found: {CLIENT_SECRET}")

    with open(CLIENT_SECRET) as f:
        raw = json.load(f)

    cred = raw.get("web") or raw.get("installed")
    if not cred:
        sys.exit("Invalid client secret file — missing 'web' or 'installed' key.")

    client_id = cred["client_id"]
    client_secret = cred["client_secret"]
    token_uri = cred.get("token_uri", "https://oauth2.googleapis.com/token")

    # Step 1 — build auth URL
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={'%20'.join(SCOPES)}"
        f"&access_type=offline"
        f"&prompt=consent"
    )

    print("=" * 60)
    print("Opening browser for Google authorization...")
    print("If it doesn't open, visit this URL manually:\n")
    print(auth_url)
    print("=" * 60)

    import webbrowser
    webbrowser.open(auth_url)

    # Start a local server to catch the redirect
    server = HTTPServer(("localhost", REDIRECT_PORT), _CallbackHandler)
    print(f"\nWaiting for Google to redirect to localhost:{REDIRECT_PORT} ...")
    server.handle_request()  # handles exactly one request then stops

    code = _auth_code
    if not code:
        sys.exit("No authorization code received.")

    # Step 2 — exchange code for tokens
    resp = _rq.post(token_uri, data={
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    })

    if resp.status_code != 200:
        sys.exit(f"Token exchange failed ({resp.status_code}):\n{resp.text}")

    token_data = resp.json()

    # Save in the format google.oauth2.credentials expects
    token_file = {
        "token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "token_uri": token_uri,
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": SCOPES,
    }

    with open(TOKEN_PATH, "w") as f:
        json.dump(token_file, f, indent=2)

    print(f"\nToken saved to: {TOKEN_PATH}")
    print("Google Drive authorization complete!")


if __name__ == "__main__":
    main()
