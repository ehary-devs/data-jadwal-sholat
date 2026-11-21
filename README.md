# data-jadwal-sholat

Jadwal sholat harian untuk 514 kabupaten/kota Indonesia, dengan kode wilayah Kepmendagri (dari repo [`data-wilayah`](../data-wilayah)). Datanya diambil dari **SIHAT (Sistem Informasi Hisab Rukyat) Kementerian Agama RI** lewat [bimasislam.kemenag.go.id/jadwal-sholat](https://bimasislam.kemenag.go.id/jadwal-sholat). Tidak dihitung sendiri dan tidak diambil dari pihak ketiga.

## Format

`data/{tahun}/{kode}.json`, contoh `data/2026/33.74.json`:

```json
{
  "kode": "33.74", "nama": "Kota Semarang", "tahun": 2026,
  "sumber": {"prov": "JAWA TENGAH", "kabko": "KOTA SEMARANG"},
  "lat": -6.983531, "lng": 110.445283,
  "waktu": ["imsak","subuh","terbit","dhuha","dzuhur","ashar","maghrib","isya"],
  "jadwal": {"2026-01-01": ["03:53","04:03", "..."], "...": []},
  "titik": [{"nama": "...", "lat": 0, "lng": 0, "jadwal": {}}]
}
```

- Jam dalam waktu setempat (WIB/WITA/WIT), urutan sesuai `waktu`.
- `lat`/`lng` adalah titik acuan hisab dari Bimas, bukan pusat wilayah.
- `titik` hanya ada kalau Bimas punya titik tambahan di wilayah itu (pulau-pulau di Kepri, Sofifi).
- `data/meta.json`: sumber, tanggal ambil, tahun, jumlah.

## Pemetaan Bimas → kode Kepmendagri

Bimas punya 517 entri dengan sebagian nama lama, dan semua kab/kota di 4 provinsi pemekaran Papua serta Papua Barat Daya masih dikelompokkan di provinsi induknya. Nama dicocokkan otomatis (`norm()` di `scripts/common.py`). Pengecualian dicatat di `checks/alias.csv`:

- **utama**: jadwal untuk kode itu. Contohnya nama lama seperti Toba Samosir → 12.12. `KOTA JAKARTA` dipakai untuk kelima kota administrasi (31.71–31.75), karena Bimas hanya punya satu titik.
- **titik**: titik tambahan, disimpan di `titik` milik kabupaten induknya.
- **abaikan**: entri ganda/usang (`KAB. YAPEN WAROPEN`).

Build gagal kalau ada entri Bimas yang tidak terpetakan, kode yang dipetakan dua kali, atau kode tanpa jadwal.

## Perintah

```sh
make fetch    # unduh ke build/raw/ (bisa dilanjutkan; ±12.400 request, ±5 jam)
make build    # pemetaan + tulis data/
make verify   # wajib lolos sebelum commit data
make test
make sync     # salin data/ ke astro-devs/public/api/jadwal-sholat/
```

`WILAYAH` (default `../data-wilayah/data/wilayah.csv`) dan `TAHUN` (default: tahun ini + tahun depan, contoh `TAHUN="2028"`) bisa diganti lewat env.

`verify` memeriksa: semua 514 kode punya file per tahun, tanggal lengkap 365/366 hari, format jam, urutan imsak < subuh < … < isya, imsak = subuh − 10 menit dan koordinat di dalam Indonesia.

## Otomatis (GitHub Actions)

`.github/workflows/update.yml` jalan tanggal 1 tiap bulan (03:00 WIB) dan bisa dipicu manual dari tab Actions:

1. `make fetch build verify` untuk tahun ini + tahun depan. Kalau ada yang gagal, job berhenti dan data lama tetap tayang.
2. Kalau jadwal berubah, `data/` di-commit ke repo ini.
3. `make sync` ke astro-devs. Kalau hasilnya beda, workflow membuat atau memperbarui PR dari branch `data/jadwal-sholat`. Setelah PR di-merge, Cloudflare Workers Builds men-deploy.

Pergantian tahun tidak perlu diurus: `TAHUN` default-nya tahun berjalan + tahun depan, dan tahun lama tetap disimpan di `data/`.

Butuh secret `ASTRO_DEVS_TOKEN`: fine-grained PAT, hanya untuk repo `ehary-devs/astro-devs`, dengan izin **Contents: Read and write** + **Pull requests: Read and write**.

Manual (cadangan): `make fetch build verify sync`, lalu commit di astro-devs.

## Kalau Bimas mengubah daftar kab/kota

Build akan gagal dan menyebut entri yang tidak terpetakan. Tambahkan entri itu ke `checks/alias.csv`.

## Catatan

API `/api/sihat/*` adalah API internal situs Bimas dan tidak didokumentasikan untuk publik. ID provinsi/kabko berupa token terenkripsi yang bisa berubah, jadi `fetch.py` selalu mengambilnya ulang dan tidak menyimpannya. Unduhan memakai 4 worker, masing-masing jeda 0,5 detik per request.

Lisensi: MIT untuk `scripts/` dan `tests/`. Data jadwal milik Kementerian Agama RI.
