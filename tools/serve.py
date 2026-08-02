#!/usr/bin/env python3
"""Serve the mirrored site locally with extensionless-URL resolution.

The live site runs Apache with a rewrite that maps /services -> services.php.
The mirror stores rendered pages as .html, so this shim resolves /services
to services.html the same way the production server does.

    python tools/serve.py          # http://localhost:8000
"""
import functools
import http.server
import os
import socketserver
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        local = super().translate_path(path)
        if not os.path.exists(local) and not os.path.splitext(local)[1]:
            if os.path.isfile(local + ".html"):
                return local + ".html"
        return local


handler = functools.partial(CleanURLHandler, directory=os.path.abspath(ROOT))
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), handler) as httpd:
    print(f"Serving mirror at http://localhost:{PORT}  (Ctrl+C to stop)")
    httpd.serve_forever()
