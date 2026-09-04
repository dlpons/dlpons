import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from anki_generator.ankiconnect import AnkiConnectClient, AnkiConnectError


def _make_handler(responses):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            length = int(self.headers["Content-Length"])
            body = json.loads(self.rfile.read(length))
            responses.append(body)
            action = body["action"]
            if action == "version":
                result, error = 6, None
            elif action == "addNote":
                result, error = 12345, None
            else:
                result, error = None, "unsupported"
            payload = json.dumps({"result": result, "error": error}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)

    return Handler


@pytest.fixture
def server():
    requests = []
    handler = _make_handler(requests)
    httpd = HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield httpd, requests
    finally:
        httpd.shutdown()
        thread.join()


def test_version(server):
    httpd, _ = server
    client = AnkiConnectClient(url=f"http://127.0.0.1:{httpd.server_port}")
    assert client.version() == 6


def test_add_note_sends_correct_payload(server):
    httpd, requests = server
    client = AnkiConnectClient(url=f"http://127.0.0.1:{httpd.server_port}")
    note_id = client.add_note(
        deck_name="Mining",
        model_name="Devin1",
        fields={"Word": "甘える", "Sentence": "", "PitchAccent": "", "Definition": "", "Nuance": "", "Audio": "", "Image": ""},
        tags=["mined"],
    )
    assert note_id == 12345
    sent = requests[0]
    assert sent["action"] == "addNote"
    assert sent["params"]["note"]["deckName"] == "Mining"
    assert sent["params"]["note"]["modelName"] == "Devin1"
    assert sent["params"]["note"]["fields"]["Word"] == "甘える"
    assert sent["params"]["note"]["tags"] == ["mined"]


def test_unreachable_server_raises():
    client = AnkiConnectClient(url="http://127.0.0.1:1", timeout=1)
    with pytest.raises(AnkiConnectError):
        client.version()
