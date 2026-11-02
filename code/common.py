"""Shared paths, model parameters and helpers for the known-world project.

Raw inputs (read in place, never modified; from step 02 on only data/ and the Natural Earth files are needed):
  /home/claude/work/known-world/expeditions/*.json
      The expedition gazetteer compiled for this study, one file per region (schema in DATA_BRIEF.md): journeys with
      leader, sponsor, years, mode (sea, land, river, sledge, air, base), dated waypoints, summary, sources, route
      confidence, notes, lost/regained flags and a viewpoint (europe, islamic, china, polynesia).
  /home/claude/work/known-world/verification.json
      An automatic check of the cited English Wikipedia article for part of the entries: id -> checked title, URL and
      whether the article's text contains the start and end years.
  /home/claude/newdata/raw/geo/ne_50m_land.geojson, ne_50m_admin_0_countries.geojson,
  ne_10m_populated_places_simple.geojson
      Natural Earth (public domain): land mask, modern borders and place names.
  /home/claude/newdata/raw/geo_extra/ne_50m_antarctic_ice_shelves_polys.geojson
      Natural Earth Antarctic ice shelves (public domain, raw.githubusercontent.com/nvkelso/natural-earth-vector). Ice
      shelves are counted as land (land or permanent ice) in the land share and drawn as land on the map.
"""
import json, gzip, os, re, unicodedata
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KW = os.environ.get("KW_RAW", "/home/claude/work/known-world")
EXPED = os.path.join(KW, "expeditions")
VERIF = os.path.join(KW, "verification.json")
GEO = os.environ.get("KW_GEO", "/home/claude/newdata/raw/geo")
# Natural Earth 50m Antarctic ice shelves (from github.com/nvkelso/natural-earth-vector), counted as land/ice
ICE = os.environ.get("KW_ICE", "/home/claude/newdata/raw/geo_extra/ne_50m_antarctic_ice_shelves_polys.geojson")
FONTS = os.environ.get("KW_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("KWTMP", "/dev/shm/known-world"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "known-world"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23897793"                 # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/known-world/"           # filled in by the publisher
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

# ---------------- reveal model (all parameters of the model live here) ----------------
H3_RES = 4                     # H3 resolution 4: 288,122 cells, average 1,770 km2 (about 42 km across)
STEP_KM = 8                    # routes are densified to a point every STEP_KM km before buffering
RADIUS_KM = {                  # how far either side of a route a cell counts as seen (cell centre within this distance)
    "sea": {"sea": 150, "land": 40},       # a ship sees open water widely and a coast only near the shore
    "land": {"sea": 120, "land": 120},
    "river": {"sea": 120, "land": 120},
    "sledge": {"sea": 120, "land": 120},
    "air": {"sea": 150, "land": 150},
    "base": {"sea": 250, "land": 250},     # starting worlds: dense points over an area already known
    "survey": {"sea": 0, "land": 0},       # survey and settlement layer: whole regions, land cells only (code/surveys.py)
}
FILL_CELLS = 150               # an unknown pocket of fewer than this many cells (about 265,000 km2, the size of the UK), wholly enclosed by known cells, counts as known
FILL_STEP = 10                 # years between the checks for enclosed pockets
YEAR0, YEAR1 = -2200, 1960     # time range of the study (BC years negative; there is no year 0 in the data)
VIEWPOINTS = ["europe", "islamic", "china", "polynesia"]
VP_NAME = {"europe": "Europe", "islamic": "the Islamic world", "china": "China", "polynesia": "Polynesia"}
VP_SHORT = {"europe": "Europe", "islamic": "Islamic world", "china": "China", "polynesia": "Polynesia"}
VP_COL = {"europe": "#B23A2A", "islamic": "#2E8A6E", "china": "#B07A12", "polynesia": "#2F5FA7"}
STATUS = ["read_by_compiler", "years_confirmed", "years_not_confirmed", "unsourced"]
CONFIRMED = ("read_by_compiler", "years_confirmed")   # the 'confirmed-only' sensitivity run keeps these
# Non-linear time scale for the slider and the video: (year, position 0..1) knots, linear between.
TIME_KNOTS = [(-2200, 0.0), (-500, 0.12), (1400, 0.36), (1960, 1.0)]

# Page raster: Web Mercator, square, covering the world between +-85.05 degrees.
RASTER = 2048
MERC_MAX = 85.0511287798
VIDEO_W = 1800                 # plate carree raster used for the video and figures (VIDEO_W x VIDEO_W/2)
COL = {"land": "#ece4d4", "sea": "#4f7fae", "dark": "#1b1b1b", "red": "#B23A2A"}


def year_pos(y):
    ys, ps = zip(*TIME_KNOTS)
    return float(np.interp(y, ys, ps))


def pos_year(p):
    ys, ps = zip(*TIME_KNOTS)
    return float(np.interp(p, ps, ys))


def yr(y):
    """Year in words for public text: 325 BC, AD 150, 1492."""
    y = int(round(y))
    if y < 0:
        return f"{-y} BC"
    if y < 1000:
        return f"AD {max(y, 1)}"
    return str(y)


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "wt", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "yr": return yr(v)
    if f == "mkm": return f"{float(v) / 1e6:.1f}"
    raise ValueError(f)


def gc_km(lat1, lon1, lat2, lon2):
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))


def unwrap(lons):
    """Make a sequence of longitudes continuous across the 180 degree meridian (values may leave -180..180)."""
    out = [float(lons[0])]
    for x in lons[1:]:
        x = float(x)
        while x - out[-1] > 180: x -= 360
        while x - out[-1] < -180: x += 360
        out.append(x)
    return out


def split_antimeridian(coords):
    """Split an unwrapped [[lon, lat], ...] line into pieces inside -180..180 (for GeoJSON)."""
    parts, cur = [], []
    shift = lambda x: ((x + 180) % 360) - 180
    for i, (x, y) in enumerate(coords):
        if i == 0:
            cur.append([shift(x), y]); continue
        x0, y0 = coords[i - 1]
        k0, k1 = np.floor((x0 + 180) / 360), np.floor((x + 180) / 360)
        if k0 != k1:
            edge = (max(k0, k1)) * 360 - 180
            t = (edge - x0) / (x - x0)
            ym = y0 + t * (y - y0)
            cur.append([180.0 if x > x0 else -180.0, ym]); parts.append(cur)
            cur = [[-180.0 if x > x0 else 180.0, ym]]
        cur.append([shift(x), y])
    parts.append(cur)
    return [p for p in parts if len(p) > 1]
