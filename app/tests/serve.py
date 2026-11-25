#!/usr/bin/env python3
"""Máy chủ tĩnh để thử site/ trên máy, có hỗ trợ HTTP Range.

`python -m http.server` không hỗ trợ Range nên trình duyệt không tua được audio.
GitHub Pages thì có, nên phải thử bằng máy chủ này để giống điều kiện thật.

Usage: python3 app/tests/serve.py [cổng=8931] [thư_mục=site]
"""
import os
import re
import sys
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        m = re.fullmatch(r"bytes=(\d*)-(\d*)", rng.strip()) if rng else None
        if not m or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        start = int(m.group(1)) if m.group(1) else max(0, size - int(m.group(2) or 0))
        end = min(int(m.group(2)), size - 1) if m.group(1) and m.group(2) else size - 1
        if start > end or start >= size:
            self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            return None
        f = open(path, "rb")
        f.seek(start)
        self._remaining = end - start + 1
        self.send_response(HTTPStatus.PARTIAL_CONTENT)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(self._remaining))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        return f

    def copyfile(self, source, outputfile):
        remaining = getattr(self, "_remaining", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        try:
            while remaining > 0:
                chunk = source.read(min(65536, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass          # trình duyệt huỷ yêu cầu khi tua: bình thường
        finally:
            self._remaining = None

    def end_headers(self):
        if "Accept-Ranges" not in "".join(str(h) for h in getattr(self, "_headers_buffer", [])):
            self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8931
    root = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "..", "site")
    handler = partial(RangeHandler, directory=os.path.abspath(root))
    print(f"http://127.0.0.1:{port}/  ->  {os.path.abspath(root)}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
