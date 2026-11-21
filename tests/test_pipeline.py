import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build import resolve  # noqa: E402
from common import dms, norm  # noqa: E402
from verify import check_file  # noqa: E402


def test_norm_matches_bimas_to_kepmendagri():
    assert norm("KAB. KEPULAUAN SIAU TAGULANDANG BIARO") == norm("Kabupaten Kep. Siau Tagulandang Biaro")
    assert norm("KAB. KEPULAUAN SERIBU") == norm("Kabupaten Administrasi Kepulauan Seribu")
    assert norm("KOTA SEMARANG") == norm("Kota Semarang")
    assert norm("KOTA SEMARANG") != norm("Kabupaten Semarang")


def test_dms():
    assert dms("6° 59' 0.71\" S") == -6.983531
    assert dms("110° 26' 43.02\" E") == 110.445283


KAB = {"31.71": "Kota Administrasi Jakarta Pusat", "31.72": "Kota Administrasi Jakarta Utara", "21.03": "Kabupaten Natuna"}
IDX = [{"prov": "DKI JAKARTA", "kabko": "KOTA JAKARTA"}, {"prov": "KEPULAUAN RIAU", "kabko": "KAB. NATUNA"},
       {"prov": "KEPULAUAN RIAU", "kabko": "PULAU LAUT KAB. NATUNA"}]
ALIAS = [{"bimas_kabko": "KOTA JAKARTA", "kode": "31.71", "peran": "utama"},
         {"bimas_kabko": "KOTA JAKARTA", "kode": "31.72", "peran": "utama"},
         {"bimas_kabko": "PULAU LAUT KAB. NATUNA", "kode": "21.03", "peran": "titik"}]


def test_resolve_alias_and_titik():
    utama, titik = resolve(IDX, KAB, ALIAS)
    assert utama["31.72"]["kabko"] == "KOTA JAKARTA"
    assert utama["21.03"]["kabko"] == "KAB. NATUNA"
    assert [t["kabko"] for t in titik["21.03"]] == ["PULAU LAUT KAB. NATUNA"]


def test_resolve_fails_on_unmapped_or_missing():
    with pytest.raises(SystemExit, match="tidak terpetakan"):
        resolve(IDX + [{"prov": "X", "kabko": "KAB. ANTAH"}], KAB, ALIAS)
    with pytest.raises(SystemExit, match="tanpa jadwal: 31.72"):
        resolve(IDX, KAB, ALIAS[:1] + ALIAS[2:])


def _file(jadwal):
    return {"kode": "33.74", "lat": -6.98, "lng": 110.44, "jadwal": jadwal}


def test_check_file():
    import datetime
    ok = ["03:43", "03:53", "05:08", "05:36", "11:25", "14:40", "17:36", "18:47"]
    days = {(datetime.date(2026, 1, 1) + datetime.timedelta(i)).isoformat(): ok for i in range(365)}
    assert check_file(_file(days), 2026) == []
    bad = dict(days, **{"2026-03-01": ["03:43", "03:53", "05:08", "05:36", "11:25", "18:40", "17:36", "18:47"]})
    assert any("urutan" in e for e in check_file(_file(bad), 2026))
    missing = dict(days)
    del missing["2026-12-31"]
    assert any("tidak lengkap" in e for e in check_file(_file(missing), 2026))
