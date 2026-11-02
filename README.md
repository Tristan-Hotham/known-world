# The Known World

How much of the Earth each tradition had written about, from the Bronze Age to 1960. A dark world lights up as travellers' accounts reached their readers: 681 dated journey routes for Europe, the Islamic world, China and Polynesia, a coarse layer of 52 regions surveyed or settled for Europe, an equal-area grid, a timeline from 2200 BC to 1960 and a switch between points of view. Every place was known to the people who lived there; this measures written (or, for Polynesia, archaeologically dated) knowledge reaching one tradition.

Interactive page: https://maps.tristanhotham.com/known-world/
Paper: https://doi.org/10.5281/zenodo.23897793
Blog post: https://blog.tristanhotham.com/2026/10/31/known-world/

## Headline results

- Europe's recorded world, share of the Earth's land (surface in brackets): 14.9% after Ptolemy in AD 150 (6.8%); 19.5% in 1400; 20.0% in 1492 (10.8%); 44.3% in 1800 (49.2%); 67.3% in 1900; 80.2% in 1960 (66.0%).
- These figures count journeys plus the survey and settlement layer. From journeys alone: 39.4% in 1800, 58.0% in 1900, 63.9% in 1960; the layer adds 16.3% of the world's land by 1960.
- Milestones: a quarter of the land lit by 1542, half by 1841 (journeys alone 1861), three quarters by 1936; half of the Earth's surface by 1809 (the sea first).
- The 1800s added the most land (23.0%); the fastest decade after 1400 was the 1870s (5.9%). The single largest step is Ptolemy's Geography, a starting-world entry.
- Other points of view: the Islamic world 16.9% of the land by 1400; China 11.5% by 1492; Polynesia 3.2% of the surface by 1400, almost all ocean. Europe leads China on land from 599 BC and is never behind the Islamic world, but with confirmed entries only the Islamic world leads until 1535.
- Known elsewhere first: China 18.8 million km2 before Europe (median 616 years earlier); Polynesia 17.2 million km2 (Hawaii settled about 1219, Cook 1778; Aotearoa about 1281, Tasman 1642); the Islamic world 12.3 million km2.
- Biggest journeys by new area lit for Europe: James Cook 1773 (8.7 million km2), Ferdinand Magellan; Juan Sebastian Elcano 1520 (6.9); on land John C. Fremont 1843.
- Last large countries to be half lit for Europe: Papua New Guinea (1933), Canada (1921), Namibia (1910). In 1960 29.4 million km2 of land is still dark (10.4 million in Antarctica); much of the rest is a gap in the data (parts of the Sahara and Sahel, central Africa, outer Indonesia, the Amazon, the Greenland ice), not in knowledge.
- Sensitivity: Europe's 1960 land share ranges from 58.1% (distances halved) to 85.5% (distances x 1.5); confirmed entries only 58.1%. The shape of the curve is the same in every variant.
- Sources: 26.7% of journeys have their years confirmed in the cited Wikipedia article by an automatic check, 59.5% were taken from the cited pages by the compiler, 11.3% have years not confirmed and 2.5% a source that could not be confirmed.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/06_build_site.py`; results embedded, map data fetched from `data/`). |
| `header.png` | Social card, 1200 x 630. |
| `data/expeditions.json`, `data/expeditions.csv` | The merged gazetteer: 681 journeys with viewpoint, leader, sponsor, years, mode, route confidence, source status, lost and regained, summary, notes (guides), sources and dated waypoints (CSV: one row per journey, without waypoints). |
| `data/routes.geojson` | Routes as MultiLineStrings split at the 180 degree meridian. |
| `data/cells.csv.gz` | Every H3 cell (resolution 4): centre, area, land, and for each viewpoint the first year, first journey, fill flag, lost and regained years. |
| `data/results.json` | Every number quoted on the page, in the paper, blog, collage and post. |
| `data/site.json`, `data/raster_*_year.png`, `data/raster_*_who.png`, `data/borders.json`, `data/coast.json` | Page data: journeys and series; per-pixel first year and first journey on a 2048 x 2048 Web Mercator grid (encoding in `code/05_site_data.py`); outlines. |
| `data/merge_log.json` | Every fix, merge, rename and replaced source in the merge. |
| `code/` | Scripts, run in order; `reveal.py` (the model), `figstyle.py`; page, paper and blog templates; `qa.js`. |
| `release/` | Paper (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`), videos (`video/`: 1920 x 1080 4.4 MB, 1080 x 1920 3.4 MB). |
| `reddit/` | Collage (`collage.py`, `known_world.png`) and post text. |

## Method in brief

- Gazetteer: 681 journeys in eight regional files compiled for this study (Europe 571, Islamic world 42, China 43, Polynesia 25), 16,038 dated waypoints. Starting worlds ("base" entries) for the Aegean, Herodotus, Ptolemy and the early Islamic and Chinese states. Polynesian dates are archaeological settlement dates.
- Survey and settlement layer (Europe only, `code/surveys.py`): 52 regions (Natural Earth first-level divisions or countries, some clipped to their settled part) lit whole from the year their systematic survey was published or settlement was general, 1734 to 1955. Dates from general knowledge of the history of cartography, marked as not confirmed; coarse by design.
- Merge: validation of coordinates and years, 3 duplicates merged, 2 renamed; four citations of a mirror site replaced with the matching English Wikipedia pages; source status from an automatic check of the cited articles and the compilers' notes.
- Grid: 288,122 H3 cells (mean 1,770 km2); land if the centre is on Natural Earth 50m land or an Antarctic ice shelf.
- Reveal: routes densified every 8 km with interpolated years; a cell is lit when its centre is within 150 km (sea) or 40 km (land) of a ship's track, 120 km of a land, river or sledge route, 150 km of a flight, 250 km of a starting-world point, in the year of the nearest point. Enclosed pockets under 150 cells (about 266,000 km2) fill from their rim. Lost knowledge goes dark unless another journey covers it. All parameters in `code/common.py`.
- Sensitivity: journeys only, distances x 0.5 and x 1.5, no fill, fills of 25 and 400 cells, confirmed entries only, no starting worlds.
- Caveats: the gazetteer leans on English-language sources and European explorers, so the other viewpoints are thin; the survey layer is coarse, unconfirmed and Europe-only; trade and missions are missing, so late shares are lower bounds; years are when journeys happened, not when accounts were published; routes are approximate.

## How to rerun

Needs Python 3 with numpy, scipy, scikit-learn, shapely, rasterio, h3 (4.x), matplotlib, Pillow and fontTools, ffmpeg, xelatex and pdftotext; node with Playwright for `code/qa.js`. Step 01 reads the regional gazetteer files and the verification file (paths in `code/common.py`); from step 02 on only `data/` and Natural Earth are needed. Intermediate files go to `/dev/shm/known-world/work` (set `KWTMP` to change).

```
python3 code/01_merge.py        # merge, validate, source status: data/expeditions.*, routes.geojson
python3 code/02_grid.py         # H3 grid, land mask, pixel lookups
python3 code/03_reveal.py       # reveal model, main and sensitivity runs, data/cells.csv.gz
python3 code/04_results.py      # data/results.json
python3 code/05_site_data.py    # rasters, site.json, outlines
python3 code/06_build_site.py   # index.html
python3 code/07_figures.py      # header, blog and paper figures
python3 code/08_video.py        # release/video
python3 code/09_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/10_readme.py       # README, LICENSE, Reddit post
python3 code/11_release.py      # blog post, Zenodo files
```

## Sources and licences

- The journey gazetteer: compiled for this study, mostly from English Wikipedia articles (CC BY-SA 4.0) and the accounts they cite, listed per journey. `data/expeditions.*` and `data/routes.geojson` are released under CC BY-SA 4.0.
- Natural Earth land, Antarctic ice shelves, countries and populated places (public domain).
- H3 (Uber, Apache 2.0); Leaflet (BSD-2). Optional relief tiles on the page: Esri.
- Inspired by the animation "World exploration from Europe's point of view".

## Citation

Hotham, T. (2026) The Known World: how much of the Earth each tradition had written about, from the Bronze Age to 1960. Zenodo. https://doi.org/10.5281/zenodo.23897793

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
