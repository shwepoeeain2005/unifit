"""Render entry point for the SQLite-backed UniFit chat API."""

from contextlib import closing
from http.server import ThreadingHTTPServer
import os
import sqlite3

from chat_server import ChatHandler, DATABASE


class RenderChatHandler(ChatHandler):
    def do_GET(self):
        if self.path != "/health":
            self.send_error(404)
            return
        try:
            with closing(sqlite3.connect(f"{DATABASE.as_uri()}?mode=ro", uri=True)) as db:
                db.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
        except sqlite3.Error:
            self.send_error(503)
            return
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    with ThreadingHTTPServer(("0.0.0.0", port), RenderChatHandler) as server:
        print(f"UniFit chat API listening on port {port}", flush=True)
        server.serve_forever()
