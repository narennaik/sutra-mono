# Sutra Mono
#   make build   – regenerate UFO sources from the skeletons, then build fonts/ttf with gftools
#   make test    – run FontBakery's Google Fonts profile
#   make proof   – render a specimen image to documentation/specimen.png

SOURCES = sources/SutraMono-Light.ufo sources/SutraMono-Regular.ufo sources/SutraMono-Bold.ufo

.PHONY: build sources test proof clean

venv/touchfile: requirements.txt
	python3 -m venv venv
	venv/bin/pip install -U pip -r requirements.txt
	touch venv/touchfile

venv-qa/touchfile: requirements-qa.txt
	python3 -m venv venv-qa
	venv-qa/bin/pip install -U pip -r requirements-qa.txt
	touch venv-qa/touchfile

sources: venv/touchfile
	venv/bin/python sources/generator/export.py

build: sources
	cd sources && PATH="$(CURDIR)/venv/bin:$$PATH" gftools builder config.yaml

test: venv-qa/touchfile
	venv-qa/bin/fontbakery check-googlefonts -l WARN --succinct \
	  --html fontbakery-report.html fonts/ttf/*.ttf

proof: venv/touchfile
	venv/bin/pip install -q pillow
	venv/bin/python sources/generator/specimen.py

clean:
	rm -rf venv venv-qa fonts/ttf/*.ttf fontbakery-report.html
