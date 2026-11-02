"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json. https://doi.org/10.5281/zenodo.23897793 and https://blog.tristanhotham.com/2026/10/31/known-world/ stay as placeholders."""
from common import *

R = jload(f"{DATA}/results.json")
D, S, M = R["data"], R["share"], R["milestones"]
VID = jload(os.path.join(ROOT, "release", "video", "sizes.json")) if os.path.exists(os.path.join(ROOT, "release", "video", "sizes.json")) else {}
pc = lambda v: f"{v:.1f}%"
B = R["before_europe"]
assert M["land"]["75"] is not None and M["land"]["90"] is None

readme = f"""# The Known World

How much of the Earth each tradition had written about, from the Bronze Age to 1960. A dark world lights up as travellers' accounts reached their readers: {D['journeys']:,} dated journey routes for Europe, the Islamic world, China and Polynesia, a coarse layer of {D['surveys']} regions surveyed or settled for Europe, an equal-area grid, a timeline from 2200 BC to 1960 and a switch between points of view. Every place was known to the people who lived there; this measures written (or, for Polynesia, archaeologically dated) knowledge reaching one tradition.

Interactive page: https://maps.tristanhotham.com/known-world/
Paper: {{https://doi.org/10.5281/zenodo.23897793}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/known-world/}}

## Headline results

- Europe's recorded world, share of the Earth's land (surface in brackets): {pc(S['europe']['150']['land'])} after Ptolemy in AD 150 ({pc(S['europe']['150']['surface'])}); {pc(S['europe']['1400']['land'])} in 1400; {pc(S['europe']['1492']['land'])} in 1492 ({pc(S['europe']['1492']['surface'])}); {pc(S['europe']['1800']['land'])} in 1800 ({pc(S['europe']['1800']['surface'])}); {pc(S['europe']['1900']['land'])} in 1900; {pc(S['europe']['1960']['land'])} in 1960 ({pc(S['europe']['1960']['surface'])}).
- These figures count journeys plus the survey and settlement layer. From journeys alone: {pc(R['journeys_only']['share']['1800']['land'])} in 1800, {pc(R['journeys_only']['share']['1900']['land'])} in 1900, {pc(R['journeys_only']['share']['1960']['land'])} in 1960; the layer adds {pc(R['survey_added_1960'])} of the world's land by 1960.
- Milestones: a quarter of the land lit by {M['land']['25']}, half by {M['land']['50']} (journeys alone {R['journeys_only']['milestones']['land']['50']}), three quarters by {M['land']['75']}; half of the Earth's surface by {M['surface']['50']} (the sea first).
- The 1800s added the most land ({pc(R['century_gain']['1800'])}); the fastest decade after 1400 was the {R['fastest']['land_decade_after_1400']}s ({pc(R['fastest']['land_gain_after_1400'])}). The single largest step is Ptolemy's Geography, a starting-world entry.
- Other points of view: the Islamic world {pc(S['islamic']['1400']['land'])} of the land by 1400; China {pc(S['china']['1492']['land'])} by 1492; Polynesia {pc(S['polynesia']['1400']['surface'])} of the surface by 1400, almost all ocean. Europe leads China on land from {yr(R['overtake']['china']['land'])} and is never behind the Islamic world, but with confirmed entries only the Islamic world leads until {R['sensitivity']['confirmed_only']['overtake_islamic']}.
- Known elsewhere first: China {B['china']['km2'] / 1e6:.1f} million km2 before Europe (median {B['china']['median_lead_years']} years earlier); Polynesia {B['polynesia']['km2'] / 1e6:.1f} million km2 (Hawaii settled about {R['regions']['hawaii']['polynesia']}, Cook {R['regions']['hawaii']['europe_earliest']}; Aotearoa about {R['regions']['new_zealand']['polynesia_earliest']}, Tasman {R['regions']['new_zealand']['europe_earliest']}); the Islamic world {B['islamic']['km2'] / 1e6:.1f} million km2.
- Biggest journeys by new area lit for Europe: {R['biggest']['all'][0]['leader']} {R['biggest']['all'][0]['start']} ({R['biggest']['all'][0]['new_km2'] / 1e6:.1f} million km2), {R['biggest']['all'][1]['leader']} {R['biggest']['all'][1]['start']} ({R['biggest']['all'][1]['new_km2'] / 1e6:.1f}); on land {R['biggest']['land'][0]['leader']} {R['biggest']['land'][0]['start']}.
- Last large countries to be half lit for Europe: {', '.join(f"{c['country']} ({c['y50']})" for c in R['last_lit']['by_half'][:3])}. In 1960 {R['last_lit']['unknown_land_1960_mkm2']} million km2 of land is still dark ({R['last_lit']['unknown_antarctica_mkm2']} million in Antarctica); much of the rest is a gap in the data (parts of the Sahara and Sahel, central Africa, outer Indonesia, the Amazon, the Greenland ice), not in knowledge.
- Sensitivity: Europe's 1960 land share ranges from {pc(R['sens_range']['land_1960_min'])} (distances halved) to {pc(R['sens_range']['land_1960_max'])} (distances x 1.5); confirmed entries only {pc(R['sensitivity']['confirmed_only']['land']['1960'])}. The shape of the curve is the same in every variant.
- Sources: {D['status_pct']['years_confirmed']}% of journeys have their years confirmed in the cited Wikipedia article by an automatic check, {D['status_pct']['read_by_compiler']}% were taken from the cited pages by the compiler, {D['status_pct']['years_not_confirmed']}% have years not confirmed and {D['status_pct']['unsourced']}% a source that could not be confirmed.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/06_build_site.py`; results embedded, map data fetched from `data/`). |
| `header.png` | Social card, 1200 x 630. |
| `data/expeditions.json`, `data/expeditions.csv` | The merged gazetteer: {D['journeys']:,} journeys with viewpoint, leader, sponsor, years, mode, route confidence, source status, lost and regained, summary, notes (guides), sources and dated waypoints (CSV: one row per journey, without waypoints). |
| `data/routes.geojson` | Routes as MultiLineStrings split at the 180 degree meridian. |
| `data/cells.csv.gz` | Every H3 cell (resolution 4): centre, area, land, and for each viewpoint the first year, first journey, fill flag, lost and regained years. |
| `data/results.json` | Every number quoted on the page, in the paper, blog, collage and post. |
| `data/site.json`, `data/raster_*_year.png`, `data/raster_*_who.png`, `data/borders.json`, `data/coast.json` | Page data: journeys and series; per-pixel first year and first journey on a 2048 x 2048 Web Mercator grid (encoding in `code/05_site_data.py`); outlines. |
| `data/merge_log.json` | Every fix, merge, rename and replaced source in the merge. |
| `code/` | Scripts, run in order; `reveal.py` (the model), `figstyle.py`; page, paper and blog templates; `qa.js`. |
| `release/` | Paper (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`), videos (`video/`: 1920 x 1080 {VID.get('1920x1080', '?')} MB, 1080 x 1920 {VID.get('1080x1920', '?')} MB). |
| `reddit/` | Collage (`collage.py`, `known_world.png`) and post text. |

## Method in brief

- Gazetteer: {D['journeys']:,} journeys in eight regional files compiled for this study (Europe {D['europe_n']}, Islamic world {D['by_viewpoint']['islamic']}, China {D['by_viewpoint']['china']}, Polynesia {D['by_viewpoint']['polynesia']}), {D['waypoints']:,} dated waypoints. Starting worlds ("base" entries) for the Aegean, Herodotus, Ptolemy and the early Islamic and Chinese states. Polynesian dates are archaeological settlement dates.
- Survey and settlement layer (Europe only, `code/surveys.py`): {D['surveys']} regions (Natural Earth first-level divisions or countries, some clipped to their settled part) lit whole from the year their systematic survey was published or settlement was general, {D['survey_first']} to {D['survey_last']}. Dates from general knowledge of the history of cartography, marked as not confirmed; coarse by design.
- Merge: validation of coordinates and years, {D['merged_duplicates']} duplicates merged, {D['renamed']} renamed; four citations of a mirror site replaced with the matching English Wikipedia pages; source status from an automatic check of the cited articles and the compilers' notes.
- Grid: {R['grid']['cells']:,} H3 cells (mean {R['grid']['mean_km2']:,} km2); land if the centre is on Natural Earth 50m land or an Antarctic ice shelf.
- Reveal: routes densified every {R['grid']['step_km']} km with interpolated years; a cell is lit when its centre is within {R['grid']['radius']['sea']['sea']} km (sea) or {R['grid']['radius']['sea']['land']} km (land) of a ship's track, {R['grid']['radius']['land']['land']} km of a land, river or sledge route, {R['grid']['radius']['air']['land']} km of a flight, {R['grid']['radius']['base']['land']} km of a starting-world point, in the year of the nearest point. Enclosed pockets under {R['grid']['fill_cells']} cells (about {R['grid']['fill_km2']:,} km2) fill from their rim. Lost knowledge goes dark unless another journey covers it. All parameters in `code/common.py`.
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

Hotham, T. (2026) The Known World: how much of the Earth each tradition had written about, from the Bronze Age to 1960. Zenodo. {{https://doi.org/10.5281/zenodo.23897793}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in readme.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/ptolemy/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures, the videos and the
derived data files in data/ are released under CC BY 4.0, except the journey
gazetteer (data/expeditions.json, data/expeditions.csv, data/routes.geojson
and the journey text in data/site.json), which draws on English Wikipedia and
is released under CC BY-SA 4.0. Natural Earth is public domain. H3 is
Apache 2.0.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] How much of the world Europe had written about or mapped, 1400 BC to 1960: {S['europe']['1492']['land']:.0f}% of the land in 1492, {S['europe']['1800']['land']:.0f}% in 1800, and the parts other traditions had recorded first

## Body

You may know the animation of world exploration from Europe's point of view. I rebuilt it as data, and tried to make it honest. I compiled {D['journeys']:,} journeys with dated routes, from Austronesian voyages out of Taiwan to 1950s crossings of Antarctica, and lit up an equal-area grid wherever a route passed close enough to describe a place. Europe starts from the Bronze Age Aegean rather than from nothing, so Ptolemy's world is already lit in AD 150 ({S['europe']['150']['land']:.0f}% of the land). Because much of the world was mapped by surveyors and settlers rather than explorers, Europe also has a coarse layer of {D['surveys']} surveyed or settled regions (US township survey, Canadian prairies, Russia, India, Australia...), which you can switch off: journeys alone reach {R['journeys_only']['share']['1960']['land']:.0f}% of the land by 1960, journeys plus surveys {S['europe']['1960']['land']:.0f}%. Then very little happens for a thousand years. Half of the Earth's surface was lit for Europe by {M['surface']['50']}, half of its land only by {M['land']['50']}, and the 1800s added the most. The interactive version lets you switch the point of view to the Islamic world, China or Polynesia: China had recorded {B['china']['km2'] / 1e6:.1f} million km2 before Europe did, and Polynesians settled Hawaii around {R['regions']['hawaii']['polynesia']}, centuries before Cook. Caveats: every dark place was known to the people living there; the gazetteer leans on English-language sources; the survey layer's dates are mine and coarse; the reveal distances are a choice (1960 land share {R['sens_range']['land_1960_min']:.0f}% to {R['sens_range']['land_1960_max']:.0f}% across variants). Interactive map: https://maps.tristanhotham.com/known-world/

## Source comment

Sources: a gazetteer of {D['journeys']:,} journey routes and {D['surveys']} survey and settlement regions compiled for this study, mostly from English Wikipedia (CC BY-SA) and the accounts it cites, with a source status for every journey; Natural Earth (land, ice shelves, countries); H3 equal-area hexagonal grid.

Tools: Python (numpy, scipy, scikit-learn, shapely, h3, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/known-world/
Paper: {{https://doi.org/10.5281/zenodo.23897793}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/known-world/}}
"""
for bad in ("—", "–", "--"):
    assert bad not in post, bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README, LICENSE, post.md written")
