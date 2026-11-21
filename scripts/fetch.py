"""Download raw monthly schedules from the Bimas Islam SIHAT API into build/raw/.

Resumable: files already on disk are skipped. Province/kabko ids are opaque tokens
that may change, so they are fetched fresh each run and never stored.
"""
import datetime
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from common import API, RAW, TAHUN, raw_path, write_json

DELAY = 0.5  # seconds between requests per worker; be gentle with a government server
WORKERS = 4
UA = "Mozilla/5.0 (compatible; data-jadwal-sholat)"


def get(path: str):
    for attempt in range(6):
        try:
            req = urllib.request.Request(API + path, headers={"Accept": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            wait = 2 ** attempt * 5
            print(f"  gagal ({e}), coba lagi {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise SystemExit(f"menyerah: {path}")


def main():
    q = urllib.parse.quote
    index = []
    for p in get("provinsi")["data"]:
        kabko = get(f"kabko?prov={q(p['id'])}")["data"]
        time.sleep(DELAY)
        index += [(p, k) for k in kabko]
    print(f"{len(index)} kab/kota dari Bimas")
    write_json(RAW / "index.json", {
        "diambil": datetime.date.today().isoformat(),
        "kabko": [{"prov": p["name"], "kabko": k["name"]} for p, k in index],
    }, pretty=True)

    for tahun in TAHUN:
        todo = [(p, k, b) for p, k in index for b in range(1, 13)
                if not raw_path(tahun, p["name"], k["name"], b).exists()]
        print(f"{tahun}: {len(todo)} bulan belum diunduh")

        def one(job):
            p, k, b = job
            r = get(f"jadwal?prov={q(p['id'])}&kabko={q(k['id'])}&thn={tahun}&bln={b:02d}")
            if r.get("status") != 1 or not r.get("data"):
                raise SystemExit(f"respons tidak valid {p['name']} / {k['name']} {tahun}-{b:02d}: {str(r)[:200]}")
            write_json(raw_path(tahun, p["name"], k["name"], b), r)
            time.sleep(DELAY)

        with ThreadPoolExecutor(WORKERS) as ex:
            for i, _ in enumerate(ex.map(one, todo), 1):
                if i % 200 == 0:
                    print(f"  {tahun}: {i}/{len(todo)}", flush=True)


if __name__ == "__main__":
    main()
