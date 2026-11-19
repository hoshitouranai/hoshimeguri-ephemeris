# Hoshimeguri Ephemeris

This repository contains the source for Hoshitouranai's annual astrological ephemeris. The charts and tables are in Japanese.

## Build an annual edition

Use Python 3.11 or later with NumPy, SciPy, Matplotlib, pyswisseph, Pillow, and PyMuPDF. Install Noto Sans CJK and FreeSerif on your system.

```sh
cd perennial/source
python build_year.py --year 2028 --months all
```

The generator accepts years from 1900 through 2099. Full-year builds were verified for 2028 and 2029. See the [source notes](perennial/source/README.md) for dependencies, input data, and verification scope.

## Preserved 2027 edition

The locked v3 edition was recorded on November 15, 2026 (JST). Its 40-page A4 landscape PDF was restored with matching page renderings and bookmarks. The annual Mercury table and monthly event tables agree on the times of all 24 Mercury events. The preserved PDF is stored with the locked materials.

PDF SHA-256: `1ceb2ab218ee33b24a9ad63624c9068812e854fc9836b63b4f744bcf602c4231`

The [January 2027 layout prototype](prototype/monthly/README.txt) includes the original Python code, inputs, zodiac color palette, and verification notes.
