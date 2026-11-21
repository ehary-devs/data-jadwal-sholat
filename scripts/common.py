"""Shared helpers data-jadwal-sholat pipeline (stdlib only)."""
import csv
import datetime
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
RAW = BUILD / "raw"
DATA = ROOT / "data"
CHECKS = ROOT / "checks"
WILAYAH = Path(os.environ.get("WILAYAH", ROOT.parent / "data-wilayah" / "data" / "wilayah.csv"))

API = "https://bimasislam.kemenag.go.id/api/sihat/"
# Tahun yang diunduh: default tahun ini + tahun depan, jadi cron tidak perlu diubah tiap tahun.
_now = datetime.date.today().year
TAHUN = [int(t) for t in os.environ.get("TAHUN", f"{_now} {_now + 1}").split()]
WAKTU = ["imsak", "subuh", "terbit", "dhuha", "dzuhur", "ashar", "maghrib", "isya"]


def norm(nama: str) -> str:
    """Key for matching Bimas names ("KAB. X") to Kepmendagri names ("Kabupaten X")."""
    s = nama.upper()
    s = re.sub(r"\bKEP\.", "KEPULAUAN", s)
    s = re.sub(r"\bKABUPATEN\b|\bKAB\.?", "KAB", s)
    s = re.sub(r"\bADMINISTRASI\b|\bADM\.?", "", s)
    return re.sub(r"[^A-Z]", "", s)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def raw_path(tahun: int, prov: str, kabko: str, bln: int) -> Path:
    return RAW / str(tahun) / f"{slug(prov)}__{slug(kabko)}__{bln:02d}.json"


def dms(s: str) -> float:
    """'6° 59\\' 0.71" S' -> -6.983531"""
    m = re.fullmatch(r"\s*(\d+)°\s*(\d+)'\s*([\d.]+)\"\s*([NSEWUTB])\s*", s)
    if not m:
        raise ValueError(f"koordinat tidak dikenali: {s!r}")
    d, mnt, det, arah = m.groups()
    v = int(d) + int(mnt) / 60 + float(det) / 3600
    return round(-v if arah in "SWB" else v, 6)


def tahun_data() -> list[int]:
    """Tahun yang ada di data/ (termasuk tahun lama yang tidak diunduh ulang)."""
    return sorted(int(p.name) for p in DATA.glob("[0-9][0-9][0-9][0-9]") if p.is_dir())


def kabkota() -> dict[str, str]:
    """kode -> nama for the 514 kab/kota rows of data-wilayah."""
    with open(WILAYAH, newline="", encoding="utf-8") as f:
        return {r["kode"]: r["nama"] for r in csv.DictReader(f) if r["kode"].count(".") == 1}


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj, pretty=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")  # rename is atomic: an interrupted run never leaves half a file
    with open(tmp, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        else:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    tmp.replace(path)
