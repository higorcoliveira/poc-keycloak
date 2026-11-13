import io
import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import HTTPServer
from unittest.mock import patch
from urllib.error import URLError

from app import Handler


class ProtectedEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def request(self, authorization=None, path="/protected"):
        connection = HTTPConnection("127.0.0.1", self.server.server_port)
        headers = {"Authorization": authorization} if authorization else {}
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def test_missing_token_and_unknown_path(self):
        self.assertEqual(self.request()[0], 401)
        self.assertEqual(self.request(path="/other")[0], 404)

    @patch("app.urlopen")
    def test_active_access_token(self, open_url):
        open_url.return_value.__enter__.return_value = io.BytesIO(json.dumps({
            "active": True,
            "client_id": "demo-api",
            "token_type": "Bearer",
            "preferred_username": "alice",
        }).encode())
        self.assertEqual(self.request("Bearer" + " sample"), (200, {"message": "Hello, alice!"}))

    @patch("app.urlopen")
    def test_rejects_inactive_wrong_client_and_refresh_tokens(self, open_url):
        for token in (
            {"active": False},
            {"active": True, "client_id": "other", "token_type": "Bearer"},
            {"active": True, "client_id": "demo-api", "token_type": "Refresh"},
        ):
            with self.subTest(token=token):
                open_url.return_value.__enter__.return_value = io.BytesIO(json.dumps(token).encode())
                self.assertEqual(self.request("Bearer" + " sample")[0], 401)

    @patch("app.urlopen", side_effect=URLError("unavailable"))
    def test_keycloak_unavailable(self, _open_url):
        self.assertEqual(self.request("Bearer" + " sample")[0], 503)


if __name__ == "__main__":
    unittest.main()
