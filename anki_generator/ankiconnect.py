"""Minimal AnkiConnect client -- https://foosoft.net/projects/anki-connect/"""

import json
import urllib.error
import urllib.request

DEFAULT_URL = "http://127.0.0.1:8765"


class AnkiConnectError(Exception):
    pass


class AnkiConnectClient:
    def __init__(self, url: str = DEFAULT_URL, timeout: float = 10.0):
        self.url = url
        self.timeout = timeout

    def _invoke(self, action: str, **params) -> object:
        payload = json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8")
        request = urllib.request.Request(self.url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise AnkiConnectError(
                f"could not reach AnkiConnect at {self.url} -- is Anki running with the add-on installed? ({exc})"
            ) from exc

        if len(body) != 2 or "error" not in body or "result" not in body:
            raise AnkiConnectError(f"unexpected AnkiConnect response: {body!r}")
        if body["error"] is not None:
            raise AnkiConnectError(body["error"])
        return body["result"]

    def version(self) -> int:
        return self._invoke("version")

    def deck_names(self) -> list[str]:
        return self._invoke("deckNames")

    def model_names(self) -> list[str]:
        return self._invoke("modelNames")

    def add_note(
        self,
        deck_name: str,
        model_name: str,
        fields: dict[str, str],
        tags: list[str] | None = None,
        allow_duplicate: bool = False,
    ) -> int:
        note = {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": fields,
            "tags": tags or [],
            "options": {
                "allowDuplicate": allow_duplicate,
                "duplicateScope": "deck",
            },
        }
        return self._invoke("addNote", note=note)
