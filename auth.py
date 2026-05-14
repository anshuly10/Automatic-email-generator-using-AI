# auth.py
# Handles Google OAuth2 authentication for Gmail + Drive
# Run once with: python auth.py

import os
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv

load_dotenv()

TOKEN_FILE = "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive.readonly",
]
REDIRECT_URI = "http://localhost:3000/oauth2callback"

# Shared variable to capture the auth code from the callback server
_auth_code = None


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
                <h2>&#10003; Authentication successful!</h2>
                <p>You can close this tab and return to the terminal.</p>
                </body></html>
            """)
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No auth code received.")

    def log_message(self, format, *args):
        pass  # Suppress request logs


def get_credentials() -> Credentials:
    """Load saved credentials or run OAuth flow if not authenticated yet."""
    creds = None

    # Load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_token(creds)
        return creds

    # Valid credentials exist
    if creds and creds.valid:
        return creds

    # First time: run OAuth flow
    return _run_oauth_flow()


def _run_oauth_flow() -> Credentials:
    global _auth_code

    client_config = {
        "web": {
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }

    flow = Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")

    print("\n🔐 Opening browser for Google authentication...")
    print(f"   If it doesn't open, visit:\n   {auth_url}\n")
    webbrowser.open(auth_url)

    # Start local server to capture the callback
    print("⏳ Waiting for Google OAuth callback on http://localhost:3000 ...")
    server = HTTPServer(("localhost", 3000), OAuthCallbackHandler)
    server.handle_request()  # Handle one request then stop

    if not _auth_code:
        raise RuntimeError("Did not receive auth code from Google.")

    flow.fetch_token(code=_auth_code)
    creds = flow.credentials
    _save_token(creds)
    print("✅ Authentication successful! token.json saved.\n")
    return creds


def _save_token(creds: Credentials):
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())


# Run directly: python auth.py
if __name__ == "__main__":
    get_credentials()
    print("You're all set! Run 'python main.py' to start the agent.")
