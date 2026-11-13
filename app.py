import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8080").rstrip("/")
CLIENT_ID = "demo-api"
CLIENT_SECRET = "demo-client-secret"


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        if status == 401:
            self.send_header("WWW-Authenticate", "Bearer")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path != "/protected":
            self.respond(404, {"error": "not found"})
            return

        parts = self.headers.get("Authorization", "").split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            self.respond(401, {"error": "bearer token required"})
            return

        request = Request(
            f"{KEYCLOAK_URL}/realms/demo/protocol/openid-connect/token/introspect",
            data=urlencode({
                "token": parts[1],
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            }).encode(),
        )
        try:
            with urlopen(request, timeout=5) as response:
                token = json.load(response)
        except (URLError, TimeoutError, ValueError, OSError):
            self.respond(503, {"error": "Keycloak unavailable"})
            return

        if (not token.get("active") or token.get("client_id") != CLIENT_ID
                or token.get("token_type") != "Bearer"):
            self.respond(401, {"error": "invalid token"})
            return

        self.respond(200, {"message": "Hello, " + token.get("preferred_username", "user") + "!"})


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
