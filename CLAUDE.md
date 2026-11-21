# data-jadwal-sholat

Baca `README.md` dulu. Aturan inti:

- Sumber data **hanya** API SIHAT Bimas Islam Kemenag (`bimasislam.kemenag.go.id/api/sihat/`). Jangan memakai API pihak ketiga, baik sebagai sumber maupun pembanding. Jangan menghitung jadwal sendiri.
- Kode wilayah mengikuti `data-wilayah` (514 kab/kota). Pengecualian nama hanya lewat `checks/alias.csv`, jangan di-hardcode di script.
- Data tidak boleh di-commit sebelum `make verify` lolos.
- Jangan perkecil `DELAY` atau menaikkan `WORKERS` di `fetch.py`, karena itu server pemerintah.
- Konsumen: `/home/qryth/projects/astrojs/astro-devs` (lewat `make sync` ke `public/api/jadwal-sholat/`).
