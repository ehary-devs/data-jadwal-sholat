"""Checks that must pass before data is committed. Exit 1 on any error."""
import datetime
import sys

from common import DATA, WAKTU, kabkota, read_json, tahun_data

TIME_FMT = "%H:%M"


def minutes(t: str) -> int:
    h, m = datetime.datetime.strptime(t, TIME_FMT).timetuple()[3:5]
    return h * 60 + m


def check_file(d: dict, tahun: int) -> list[str]:
    errs, k = [], d.get("kode")
    hari = (datetime.date(tahun + 1, 1, 1) - datetime.date(tahun, 1, 1)).days
    expected = [(datetime.date(tahun, 1, 1) + datetime.timedelta(i)).isoformat() for i in range(hari)]
    if list(d["jadwal"]) != expected:
        errs.append(f"{k} {tahun}: tanggal tidak lengkap/urut ({len(d['jadwal'])}/{hari} hari)")
    if not (-11 <= d["lat"] <= 6 and 95 <= d["lng"] <= 141):
        errs.append(f"{k}: koordinat di luar Indonesia ({d['lat']}, {d['lng']})")
    for tgl, w in d["jadwal"].items():
        try:
            m = [minutes(x) for x in w]
        except ValueError:
            errs.append(f"{k} {tgl}: format jam salah {w}")
            continue
        if len(m) != len(WAKTU) or m != sorted(set(m)):
            errs.append(f"{k} {tgl}: urutan waktu salah {w}")
        elif m[1] - m[0] != 10:
            errs.append(f"{k} {tgl}: imsak bukan subuh-10 menit {w}")
    return errs


def check_coverage(kab: dict, files: dict, years: list[int]) -> list[str]:
    return [f"file hilang: {t}/{k}.json ({n})" for t in years for k, n in kab.items() if (t, k) not in files]


def main():
    kab = kabkota()
    years = tahun_data()
    if not years:
        sys.exit("data/ kosong, jalankan make build dulu")
    files = {(t, p.stem): read_json(p) for t in years for p in sorted((DATA / str(t)).glob("*.json"))}
    errs = check_coverage(kab, files, years)
    for (t, _), d in files.items():
        errs += check_file(d, t)
        errs += [e for x in d.get("titik", []) for e in check_file({**x, "kode": f"{d['kode']}/{x['nama']}"}, t)]
    print(f"{len(files)} file diperiksa, {len(errs)} masalah")
    for e in errs[:50]:
        print(" ", e)
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
