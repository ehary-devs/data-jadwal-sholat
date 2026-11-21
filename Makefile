PY := python3
ASTRO_DEVS ?= ../astrojs/astro-devs
WILAYAH ?= ../data-wilayah/data/wilayah.csv
export WILAYAH

.PHONY: all fetch build verify test sync clean

all: build verify

fetch:
	cd scripts && $(PY) fetch.py

build:
	cd scripts && $(PY) build.py

verify:
	cd scripts && $(PY) verify.py

test:
	$(PY) -m pytest -q tests

sync: verify
	rm -rf $(ASTRO_DEVS)/public/api/jadwal-sholat
	mkdir -p $(ASTRO_DEVS)/public/api/jadwal-sholat
	cp -r data/. $(ASTRO_DEVS)/public/api/jadwal-sholat/

clean:
	rm -rf build
