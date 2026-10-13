"""Dashboard web lokal untuk mengelola produksi video.

Jalankan: python dashboard.py   lalu buka http://127.0.0.1:8000
"""
import argparse
import json
import mimetypes
import os
import re
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

import concepts
import production
from engine import FPS, WINNER_SECONDS, Cancelled

ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(ROOT, "dashboard")
SAFE_FILE = re.compile(r"^[\w\-]+\.(mp4|json)$")
FINISHED = ("selesai", "gagal", "dibatalkan")


class JobQueue:
    """Antrean render; satu worker agar CPU tidak kewalahan."""

    def __init__(self, out_dir):
        self.out_dir = out_dir
        self.jobs = []
        self.cond = threading.Condition()
        threading.Thread(target=self._worker, daemon=True).start()

    def add(self, konsep, mode, seed, count, audio, max_seconds):
        created = []
        with self.cond:
            for i in range(count):
                job = {"id": uuid.uuid4().hex[:8], "konsep": konsep, "mode": mode,
                       "seed": None if seed is None else seed + i, "audio": audio,
                       "max_seconds": max_seconds, "status": "antre", "progress": 0,
                       "detik_video": 0, "pesan": "", "hasil": None, "dibuat": time.time(),
                       "batal": False}
                self.jobs.append(job)
                created.append(job)
            self.cond.notify()
        return [self.public(j) for j in created]

    def cancel(self, job_id):
        with self.cond:
            for j in self.jobs:
                if j["id"] == job_id and j["status"] not in FINISHED:
                    j["batal"] = True
                    if j["status"] == "antre":
                        j["status"] = "dibatalkan"
                    return True
        return False

    def clear_finished(self):
        with self.cond:
            self.jobs = [j for j in self.jobs if j["status"] not in FINISHED]

    def list(self):
        with self.cond:
            return [self.public(j) for j in reversed(self.jobs)]

    @staticmethod
    def public(job):
        return {k: v for k, v in job.items() if k != "batal"}

    def _next(self):
        with self.cond:
            while True:
                for j in self.jobs:
                    if j["status"] == "antre":
                        j["status"], j["mulai"] = "berjalan", time.time()
                        return j
                self.cond.wait()

    def _worker(self):
        while True:
            job = self._next()
            concept = concepts.CONCEPTS[job["konsep"]].CONCEPT
            max_seconds = job["max_seconds"] or concept["durasi_maks"]
            total = (max_seconds + WINNER_SECONDS) * FPS

            def progress(frames, job=job):
                if job["batal"]:
                    raise Cancelled()
                job["progress"] = min(99, round(100 * frames / total, 1))
                job["detik_video"] = round(frames / FPS, 1)

            try:
                meta = production.produce(job["konsep"], job["mode"], job["seed"], self.out_dir,
                                          job["audio"], max_seconds, progress)
                job.update(status="selesai", progress=100,
                           hasil={"file": os.path.basename(meta["output"]),
                                  "judul": meta["judul"], "pemenang": meta["pemenang"],
                                  "seed": meta["seed"], "mode": meta["mode"]})
            except Cancelled:
                job["status"] = "dibatalkan"
            except Exception as e:   # tampilkan di dashboard, jangan matikan worker
                job.update(status="gagal", pesan=str(e))
            job["selesai"] = time.time()


class Handler(BaseHTTPRequestHandler):
    server_version = "StudioSimulasi/1.0"
    out_dir = production.OUT_DIR
    jobs = None

    def log_message(self, fmt, *args):
        pass

    # ---- util ----
    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def _file(self, path):
        if not os.path.isfile(path):
            return self._json({"error": "File tidak ditemukan"}, 404)
        size = os.path.getsize(path)
        start, end = 0, size - 1
        m = re.match(r"bytes=(\d*)-(\d*)$", self.headers.get("Range", ""))
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                start = int(m.group(1))
                end = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
            else:
                start = max(0, size - int(m.group(2)))
            if start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        if ctype.startswith("text/"):
            ctype += "; charset=utf-8"
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        try:
            with open(path, "rb") as f:
                f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = f.read(min(256 * 1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except (ConnectionError, OSError):
            pass   # pemutar video sering memutus koneksi saat seek

    # ---- rute ----
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._file(os.path.join(STATIC, "index.html"))
        if path == "/api/konsep":
            return self._json(concepts.info())
        if path == "/api/video":
            return self._json(production.load_videos(self.out_dir))
        if path == "/api/job":
            return self._json(self.jobs.list())
        if path == "/api/klasemen":
            return self._json(production.standings(production.load_videos(self.out_dir)))
        if path.startswith("/output/"):
            name = unquote(path[len("/output/"):])
            if SAFE_FILE.match(name):
                return self._file(os.path.join(self.out_dir, name))
        self._json({"error": "Tidak ditemukan"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/job":
            try:
                data = self._body()
                return self._json(self.jobs.add(*validate_job(data)), 201)
            except (ValueError, TypeError) as e:
                return self._json({"error": str(e)}, 400)
        m = re.fullmatch(r"/api/job/(\w+)/batal", path)
        if m:
            ok = self.jobs.cancel(m.group(1))
            return self._json({"ok": ok}, 200 if ok else 404)
        if path == "/api/job/bersihkan":
            self.jobs.clear_finished()
            return self._json({"ok": True})
        self._json({"error": "Tidak ditemukan"}, 404)

    def do_DELETE(self):
        path = urlparse(self.path).path
        m = re.fullmatch(r"/api/video/([\w\-]+\.mp4)", unquote(path))
        if m and production.delete_video(m.group(1), self.out_dir):
            return self._json({"ok": True})
        self._json({"error": "Video tidak ditemukan"}, 404)


def validate_job(data):
    konsep = data.get("konsep")
    if konsep not in concepts.CONCEPTS:
        raise ValueError("Konsep tidak dikenal")
    mode = data.get("mode") or "acak"
    if mode != "acak" and mode not in concepts.CONCEPTS[konsep].CONCEPT["mode"]:
        raise ValueError(f"Mode '{mode}' tidak tersedia untuk konsep ini")
    count = int(data.get("jumlah") or 1)
    if not 1 <= count <= 50:
        raise ValueError("Jumlah video harus 1-50")
    seed = data.get("seed")
    seed = None if seed in (None, "") else int(seed)
    if seed is not None and not 0 <= seed < 2 ** 31:
        raise ValueError("Seed harus 0 sampai 2147483647")
    max_seconds = data.get("durasi_maks")
    max_seconds = None if max_seconds in (None, "") else int(max_seconds)
    if max_seconds is not None and not 5 <= max_seconds <= 300:
        raise ValueError("Durasi maksimum harus 5-300 detik")
    return konsep, mode, seed, count, bool(data.get("audio", True)), max_seconds


def main():
    ap = argparse.ArgumentParser(description="Dashboard pengelola produksi video.")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--out", default=production.OUT_DIR, help="folder hasil video")
    ap.add_argument("--no-browser", action="store_true", help="jangan buka browser otomatis")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    Handler.out_dir = args.out
    Handler.jobs = JobQueue(args.out)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}"
    print(f"Dashboard berjalan di {url}  (Ctrl+C untuk berhenti)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard dihentikan.")


if __name__ == "__main__":
    main()
