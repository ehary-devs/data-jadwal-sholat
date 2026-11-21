"""Map Bimas kab/kota to Kepmendagri codes and write data/{tahun}/{kode}.json + data/meta.json."""
from collections import defaultdict

from common import CHECKS, DATA, RAW, TAHUN, WAKTU, dms, kabkota, norm, raw_path, read_csv, read_json, tahun_data, write_json


def resolve(index, kab, alias):
    """Return (utama: kode -> entry, titik: kode -> [entries]); raise on any gap or conflict."""
    by_name = {norm(n): k for k, n in kab.items()}
    utama, titik, errors = {}, defaultdict(list), []
    alias_by_name = defaultdict(list)
    for a in alias:
        alias_by_name[a["bimas_kabko"]].append(a)
    for e in index:
        rows = alias_by_name.pop(e["kabko"], None)
        if rows is None:
            kode = by_name.get(norm(e["kabko"]))
            rows = [{"kode": kode, "peran": "utama"}] if kode else []
        if not rows:
            errors.append(f"tidak terpetakan: {e['prov']} / {e['kabko']} (tambahkan ke checks/alias.csv)")
        for r in rows:
            if r["kode"] not in kab:
                errors.append(f"kode {r['kode']} untuk {e['kabko']} tidak ada di data-wilayah")
            elif r["peran"] == "utama":
                if r["kode"] in utama:
                    errors.append(f"kode {r['kode']} dipetakan dua kali: {utama[r['kode']]['kabko']} & {e['kabko']}")
                utama[r["kode"]] = e
            elif r["peran"] == "titik":
                titik[r["kode"]].append(e)
    errors += [f"alias tidak terpakai: {n}" for n in alias_by_name]
    errors += [f"tanpa jadwal: {k} {kab[k]}" for k in kab if k not in utama]
    if errors:
        raise SystemExit("\n".join(errors))
    return utama, titik


def load_year(tahun, e):
    jadwal, info = {}, None
    for b in range(1, 13):
        r = read_json(raw_path(tahun, e["prov"], e["kabko"], b))
        info = r
        for tgl, d in r["data"].items():
            jadwal[tgl] = [d[w] for w in WAKTU]
    return {"lat": dms(info["lintang"]), "lng": dms(info["bujur"]), "jadwal": dict(sorted(jadwal.items()))}


def main():
    kab = kabkota()
    idx = read_json(RAW / "index.json")
    utama, titik = resolve(idx["kabko"], kab, read_csv(CHECKS / "alias.csv"))
    for tahun in TAHUN:
        for kode, e in sorted(utama.items()):
            y = load_year(tahun, e)
            out = {"kode": kode, "nama": kab[kode], "tahun": tahun, "sumber": e,
                   "lat": y["lat"], "lng": y["lng"], "waktu": WAKTU, "jadwal": y["jadwal"]}
            if titik.get(kode):
                out["titik"] = [{"nama": t["kabko"], **load_year(tahun, t)} for t in titik[kode]]
            write_json(DATA / str(tahun) / f"{kode}.json", out)
        print(f"{tahun}: {len(utama)} file")
    write_json(DATA / "meta.json", {
        "sumber": "Sistem Informasi Hisab Rukyat (SIHAT) Kementerian Agama RI via https://bimasislam.kemenag.go.id/jadwal-sholat",
        "diambil": idx["diambil"],
        "tahun": tahun_data(),
        "kabkota": len(utama),
        "titik_tambahan": sum(len(v) for v in titik.values()),
        "waktu": WAKTU,
        "zona_waktu": "waktu setempat (WIB/WITA/WIT sesuai lokasi)",
    }, pretty=True)


if __name__ == "__main__":
    main()
