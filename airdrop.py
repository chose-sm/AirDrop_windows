"""AirDrop pre Windows - prenos suborov medzi PC a iPhonom cez lokalnu siet.

Spusti:  python airdrop.py   (alebo dvojklik na start.bat)
Na PC sa otvori prehliadac s QR kodom, iPhone ho naskenuje fotoaparatom.
"""
import http.cookies
import json
import mimetypes
import os
import re
import secrets
import socket
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(os.environ.get("AIRDROP_PORT", "8765"))
BASE = Path(__file__).resolve().parent
DATA = Path(os.environ.get("AIRDROP_DIR", r"F:\AirDrop"))
BOXES = {
    "inbox": DATA / "Prijate",     # z iPhonu do PC
    "outbox": DATA / "Odoslane",   # z PC do mobilu
}
CHUNK = 1024 * 1024
LOCK = threading.Lock()
TOKEN = ""

for ext, ctype in ((".heic", "image/heic"), (".heif", "image/heif"), (".mov", "video/quicktime"),
                   (".mp4", "video/mp4"), (".js", "text/javascript"), (".webp", "image/webp")):
    mimetypes.add_type(ctype, ext)


def load_token():
    """Pristupovy kluc je ulozeny, aby zalozka na iPhone fungovala aj po restarte."""
    f = DATA / ".token"
    if f.exists():
        t = f.read_text().strip()
        if t:
            return t
    t = secrets.token_urlsafe(9)
    f.write_text(t)
    return t


def lan_ips():
    ips = []
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ips.append(s.getsockname()[0])
    except OSError:
        pass
    finally:
        s.close()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips and not ip.startswith(("127.", "169.254.")):
                ips.append(ip)
    except OSError:
        pass
    return ips or ["127.0.0.1"]


def safe_name(name):
    name = os.path.basename(name.replace("\\", "/")).strip().strip(".")
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name[:200] or "subor"


def unique_path(folder, name):
    p = folder / name
    i = 1
    while p.exists():
        p = folder / f"{Path(name).stem} ({i}){Path(name).suffix}"
        i += 1
    return p


def listing(box):
    items = []
    for p in BOXES[box].iterdir():
        if p.is_file() and not p.name.startswith("."):
            st = p.stat()
            items.append({"name": p.name, "size": st.st_size, "time": st.st_ctime,
                          "type": mimetypes.guess_type(p.name)[0] or ""})
    items.sort(key=lambda x: x["time"], reverse=True)
    return items


def resolve(box, name):
    if box not in BOXES:
        return None
    folder = BOXES[box].resolve()
    p = (folder / name).resolve()
    if p.parent != folder or not p.is_file() or p.name.startswith("."):
        return None
    return p


class Handler(BaseHTTPRequestHandler):
    server_version = "AirDropWin/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    # --- pomocne ---------------------------------------------------------
    @property
    def local(self):
        return self.client_address[0] in ("127.0.0.1", "::1")

    def parse(self):
        u = urllib.parse.urlsplit(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        return urllib.parse.unquote(u.path), q

    def authed(self, q):
        if self.local or secrets.compare_digest(q.get("k", ""), TOKEN):
            return True
        c = http.cookies.SimpleCookie(self.headers.get("Cookie", ""))
        return "ad" in c and secrets.compare_digest(c["ad"].value, TOKEN)

    def send(self, code, body=b"", ctype="text/plain; charset=utf-8", headers=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, obj):
        self.send(200, json.dumps(obj), "application/json; charset=utf-8")

    def send_file(self, path, attach):
        size = path.stat().st_size
        start, end, code = 0, size - 1, 200
        m = re.match(r"bytes=(\d*)-(\d*)$", self.headers.get("Range", "").strip())
        if m and size and m.group(0) != "bytes=-":
            s, e = m.groups()
            if s == "":
                start = max(0, size - int(e))
            else:
                start = int(s)
                end = min(int(e), size - 1) if e else size - 1
            if start > end or start >= size:
                return self.send(416, headers={"Content-Range": f"bytes */{size}"})
            code = 206
        self.send_response(code)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        if code == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        disp = "attachment" if attach else "inline"
        self.send_header("Content-Disposition",
                         f"{disp}; filename*=UTF-8''{urllib.parse.quote(path.name)}")
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start)
            left = end - start + 1
            while left > 0:
                chunk = f.read(min(CHUNK, left))
                if not chunk:
                    break
                self.wfile.write(chunk)
                left -= len(chunk)

    # --- GET -------------------------------------------------------------
    def do_GET(self):
        path, q = self.parse()
        if path == "/favicon.ico":
            return self.send(204)
        if not self.authed(q):
            return self.send(403, "<meta name=viewport content='width=device-width'>"
                                  "<h2 style='font-family:sans-serif'>Naskenuj znovu QR kód z PC.<br>"
                                  "Scan the QR code on the PC again.</h2>",
                             "text/html; charset=utf-8")
        if path == "/":
            headers = {}
            if not self.local:
                headers["Set-Cookie"] = f"ad={TOKEN}; Path=/; Max-Age=31536000; SameSite=Strict; HttpOnly"
            html = (BASE / "index.html").read_bytes()
            return self.send(200, html, "text/html; charset=utf-8", headers)
        if path == "/api/state":
            data = {"local": self.local, "outbox": listing("outbox")}
            if self.local:
                data["inbox"] = listing("inbox")
                data["urls"] = [f"http://{ip}:{PORT}/?k={TOKEN}" for ip in lan_ips()]
                data["folder"] = str(DATA)
            return self.send_json(data)
        m = re.match(r"^/f/(inbox|outbox)/(.+)$", path)
        if m:
            box, name = m.groups()
            if box == "inbox" and not self.local:
                return self.send(403)
            p = resolve(box, name)
            if not p:
                return self.send(404, "Súbor neexistuje.")
            try:
                return self.send_file(p, q.get("dl") == "1")
            except (ConnectionError, OSError):
                return
        self.send(404)

    # --- POST ------------------------------------------------------------
    def do_POST(self):
        path, q = self.parse()
        if not self.authed(q):
            return self.send(403)
        if path == "/api/upload":
            return self.upload(q)
        if not self.local:
            return self.send(403)
        if path == "/api/delete":
            p = resolve(q.get("box", ""), q.get("name", ""))
            if p:
                p.unlink()
            return self.send_json({"ok": True})
        if path == "/api/clear":
            for item in listing("outbox"):
                (BOXES["outbox"] / item["name"]).unlink(missing_ok=True)
            return self.send_json({"ok": True})
        if path == "/api/open":
            box = q.get("box", "inbox")
            p = resolve(box, q["name"]) if q.get("name") else BOXES.get(box)
            if p:
                os.startfile(str(p))
            return self.send_json({"ok": True})
        self.send(404)

    def upload(self, q):
        # z PC ide subor do "Odoslane", z iPhonu do "Prijate"
        folder = BOXES["outbox" if self.local else "inbox"]
        name = safe_name(q.get("name", "subor"))
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self.send(411, "Chýba Content-Length.")
        tmp = folder / f".{secrets.token_hex(6)}.part"
        try:
            with open(tmp, "wb") as f:
                left = length
                while left > 0:
                    chunk = self.rfile.read(min(CHUNK, left))
                    if not chunk:
                        raise ConnectionError("prerusene nahravanie")
                    f.write(chunk)
                    left -= len(chunk)
            with LOCK:
                final = unique_path(folder, name)
                os.replace(tmp, final)
            mtime = q.get("mtime", "")
            if mtime.isdigit():
                os.utime(final, (int(mtime) / 1000, int(mtime) / 1000))
        except (ConnectionError, OSError) as e:
            tmp.unlink(missing_ok=True)
            self.close_connection = True
            print(f"  ! Chyba pri prijímaní {name}: {e}")
            return
        who = "PC -> iPhone" if self.local else "iPhone -> PC"
        print(f"  {who}: {final.name} ({length / 1048576:.1f} MB)")
        self.send_json({"ok": True, "name": final.name})


def main():
    global TOKEN
    old_outbox = DATA / "Na iPhone"  # nazov z predchadzajucej verzie
    if old_outbox.is_dir() and not BOXES["outbox"].exists():
        old_outbox.rename(BOXES["outbox"])
    for folder in BOXES.values():
        folder.mkdir(parents=True, exist_ok=True)
    for stale in DATA.glob("*/.*.part"):
        stale.unlink(missing_ok=True)
    TOKEN = load_token()
    try:
        srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    except OSError:
        print(f"Port {PORT} je obsadený - AirDrop už pravdepodobne beží.")
        webbrowser.open(f"http://localhost:{PORT}/")
        return
    srv.daemon_threads = True
    print("AirDrop pre Windows beží.")
    print(f"  Priečinok: {DATA}")
    for ip in lan_ips():
        print(f"  Adresa pre iPhone: http://{ip}:{PORT}/?k={TOKEN}")
    print("  Ukonči Ctrl+C.\n")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.5, webbrowser.open, [f"http://localhost:{PORT}/"]).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("Ukončené.")


if __name__ == "__main__":
    main()
