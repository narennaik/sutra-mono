# Sutra Mono

![Sutra Mono specimen](documentation/specimen.png)

Sutra Mono is a monospaced typeface for code, drawn as a single thread. Every letter is one
centre-line traced with a round pen: terminals end in the same soft curve, nothing has a sharp
corner, and weight is a single number.

- **Weights:** Light, Regular, Bold
- **Coverage:** GF Latin Core (Western, Central and South-East European Latin), plus a set of
  mathematical and functional-programming symbols: ∘ → ← ⇒ ⇐ ↦ λ ∀ ∃ ≡ ≠ ≅ ≤ ≥ ⊗ ⊕ × ∈ ⊥ ⊤ ∅ ¬
- **Licence:** [SIL Open Font License 1.1](OFL.txt)

## Design document

[Sutra Mono: the design document (PDF)](documentation/design-doc/Sutra-Mono-Design-Document.pdf) tells
the story of the font: the single-pen idea, the soft-square curve, the grid, the shared bowl, the
composition set and the optical corrections in 1.100. It is generated from the font itself by
[`make_doc.py`](documentation/design-doc/make_doc.py); run `make doc` to rebuild it.

## Install

Download the `.ttf` files from [`fonts/ttf`](fonts/ttf) and install them, then set your editor's
font, for example `"editor.fontFamily": "Sutra Mono"` in VS Code or `font-family = Sutra Mono` in
Ghostty.

## How the font is made

The design lives in code. [`sources/generator/skeletons.py`](sources/generator/skeletons.py)
describes every glyph as centre-line paths on a 1000-unit em with a 600-unit advance.
[`geometry.py`](sources/generator/geometry.py) sweeps an elliptical pen along those paths and fits
the result to cubic Bézier contours with nodes at extrema, and
[`export.py`](sources/generator/export.py) writes one UFO per weight, with accented letters as
components and mark anchors for combining accents. The UFOs in [`sources`](sources) are committed
and are what `gftools builder` compiles.

## Build

Requires Python 3.10 or later.

```
make build    # regenerate the UFO sources, then build fonts/ttf
make test     # FontBakery, Google Fonts profile
make proof    # render documentation/specimen.png
```

## Changelog

**1.100**: Elliptical pen (horizontals 8% lighter); redrawn s, S, $, r; GF Latin Core coverage;
curve-fitted outlines; UFO sources and a gftools build.

**1.000**: First release.

## Licence

This Font Software is licensed under the SIL Open Font License, Version 1.1. The licence is copied
in [OFL.txt](OFL.txt) and is also available with a FAQ at https://openfontlicense.org.
