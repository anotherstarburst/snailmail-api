import base64, json, re, requests
from contextlib import contextmanager
from flask import request
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token
from app.errors import ClientDisconnectError

def get_authenticated_headers(service_url: str) -> dict:
    auth_req = GoogleAuthRequest()
    token = google_id_token.fetch_id_token(auth_req, service_url)
    return {"Authorization": f"Bearer {token}"}

@contextmanager
def request_timeout_handler():
    def check_client_connected():
        if request.environ.get('werkzeug.socket'):
            try: request.environ['werkzeug.socket'].getpeername()
            except: raise ClientDisconnectError("Client disconnected")
    yield check_client_connected
