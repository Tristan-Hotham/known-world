"""Page data: per-viewpoint rasters, journeys, series, places, borders and coastlines.

data/raster_<vp>_year.png   Web Mercator, RASTER x RASTER, 8-bit RGB. R*256+G = first year + 2500 (65535: not known by 1960);
                            B bit 0 = land pixel (Natural Earth land and Antarctic ice shelves); B >> 1 = row+1 in the
                            viewpoint's lost table (0: never lost).
data/raster_<vp>_who.png    same grid. R*256+G = 1 + index of the first journey in site.json (0: none); B = 1 if the cell was
                            filled as an enclosed pocket.
data/site.json              journeys (with unwrapped routes and dated points), yearly shares by viewpoint, lost tables,
                            key moments, places for search and the time scale.
data/borders.json, data/coast.json   simplified Natural Earth borders and coastlines (lazy-loaded layers)."""
import pickle
from PIL import Image
import shapely
from shapely.geometry import shape, mapping
from reveal import *

J = jload(f"{DATA}/expeditions.json")
R = jload(f"{DATA}/results.json")
S = pickle.load(open(f"{WORK}/state_main.pkl", "rb"))
S["europe_j"] = pickle.load(open(f"{WORK}/state_journeys_only.pkl", "rb"))["europe"]      # Europe from journeys alone
KEYS = VIEWPOINTS + ["europe_j"]
PM = np.load(f"{WORK}/pix_merc.npz"); pcell, pland = PM["cell"], PM["land"]
GI = {e["id"]: i for i, e in enumerate(J)}
NEWA = {}
for vp in VIEWPOINTS:
    s = S[vp]
    m = s["by"] >= 0
    a = np.bincount(s["by"][m], weights=AREA[m], minlength=len(s["ids"]))
    for k, jid in enumerate(s["ids"]):
        NEWA[jid] = int(round(a[k], -3))

LOST = {}
for vp in KEYS:
    s = S[vp]
    first = s["first"][pcell]; lost = s["lost"][pcell]; reg = s["regained"][pcell]
    pairs = sorted({(int(a), int(b)) for a, b in zip(s["lost"][s["lost"] < NEVER], s["regained"][s["lost"] < NEVER])})
    assert len(pairs) < 127, len(pairs)
    LOST[vp] = [[a, b if b < NEVER else None] for a, b in pairs]
    lidx = np.zeros(pcell.shape, np.uint8)
    for k, (a, b) in enumerate(pairs):
        lidx[(lost == a) & (reg == b)] = k + 1
    yv = np.where(first < NEVER, first + 2500, 65535).astype(np.uint32)
    img = np.stack([(yv >> 8).astype(np.uint8), (yv & 255).astype(np.uint8), (pland.astype(np.uint8) | (lidx << 1))], -1)
    Image.fromarray(img, "RGB").save(f"{DATA}/raster_{vp}_year.png", optimize=True)
    by = s["by"][pcell]
    gidx = np.array([GI[j] for j in s["ids"]] + [-1])
    wv = (np.where(by >= 0, gidx[by] + 1, 0)).astype(np.uint32)
    img = np.stack([(wv >> 8).astype(np.uint8), (wv & 255).astype(np.uint8), s["filled"][pcell].astype(np.uint8)], -1)
    Image.fromarray(img, "RGB").save(f"{DATA}/raster_{vp}_who.png", optimize=True)
    print(vp, os.path.getsize(f"{DATA}/raster_{vp}_year.png") // 1024, "KB year,", os.path.getsize(f"{DATA}/raster_{vp}_who.png") // 1024, "KB who")

# journeys
GUIDE = re.compile(r"[^.]*\b(guide[sd]?|guiding|interpret\w*|pilot|navigator|pundit)\b[^.]*\.", re.I)
JS = []
for e in J:
    xs = unwrap([p[0] for p in e["waypoints"]])
    pts = []
    for x, p in zip(xs, e["waypoints"]):
        pts += [round(x, 2), round(p[1], 2), p[2]]
    g = " ".join(m.group(0).strip() for m in GUIDE.finditer(e["notes"] or ""))
    JS.append({"id": e["id"], "l": e["label"], "n": e["leader"], "sp": e["sponsor"], "s": e["start"], "e": e["end"], "m": e["mode"],
               "v": e["viewpoint"], "st": e["source_status"], "c": e.get("route_confidence"), "sum": e["summary"], "g": g or None,
               "src": e["sources"][:3], "lost": e["lost"], "a": NEWA.get(e["id"], 0), "p": pts})

YRS = np.arange(YEAR0, YEAR1 + 1)
SER = {vp: series(S[vp]) for vp in KEYS}
SITE = {"journeys": JS, "y0": YEAR0, "y1": YEAR1, "knots": TIME_KNOTS, "lost": LOST,
        "series": {vp: {k: [int(round(v * 10000)) for v in SER[vp][k]] for k in ("land", "surface")} for vp in KEYS},
        "vp": {vp: {"name": VP_SHORT[vp], "col": VP_COL[vp]} for vp in VIEWPOINTS}}
# 'all compared': known to any viewpoint
Uf = np.minimum.reduce([np.where((S[vp]["lost"] < NEVER) & (S[vp]["regained"] >= NEVER), NEVER, S[vp]["first"]) for vp in VIEWPOINTS])
su = series({"first": Uf, "lost": np.full(NC, NEVER), "regained": np.full(NC, NEVER)})
SITE["series"]["all"] = {k: [int(round(v * 10000)) for v in su[k]] for k in ("land", "surface")}
Uj = np.minimum(Uf, NEVER)
Uj = np.minimum.reduce([np.where((S[vp]["lost"] < NEVER) & (S[vp]["regained"] >= NEVER), NEVER, S[vp]["first"]) for vp in ("europe_j", "islamic", "china", "polynesia")])
suj = series({"first": Uj, "lost": np.full(NC, NEVER), "regained": np.full(NC, NEVER)})
SITE["series"]["all_j"] = {k: [int(round(v * 10000)) for v in suj[k]] for k in ("land", "surface")}
assert abs(SITE["series"]["europe"]["land"][1960 - YEAR0] / 100 - R["share"]["europe"]["1960"]["land"]) < .06

# key moments: (year, journey id or None, viewpoint, title, text)
MOM = [(-2200, "austronesian-taiwan-1500", "polynesia", "Out of Taiwan", "Austronesian voyagers move south into the Philippines: the start of the greatest seafaring expansion before 1500."),
       (-1400, "base-aegean-bronze-age", "europe", "The Aegean world", "The starting point for Europe: the Mycenaean and Minoan seas, known from pottery, palaces and Egyptian and Hittite records."),
       (-600, "necho-phoenicians-600", "europe", "Round Africa?", "Herodotus reports Phoenicians sent by Pharaoh Necho sailing round Africa. Nobody followed, and the knowledge was lost."),
       (-325, None, "europe", "Pytheas and Alexander", "Pytheas sails to Britain and the northern ocean; Alexander's army and Nearchus's fleet carry Greek eyes to the Indus."),
       (-138, "zhang-qian-138", "china", "Zhang Qian goes west", "The Han envoy reaches Ferghana and Bactria and brings back the first Chinese account of Central Asia."),
       (150, None, "europe", "Ptolemy's world", "Ptolemy's Geography sums up what Rome knew, from Ireland to the edge of China."),
       (1000, "leif-1000", "europe", "Vinland", "Norse sailors reach North America. The sagas kept the memory, but Europe's maps lost it."),
       (1280, None, "polynesia", "Aotearoa", "Polynesian voyagers settle New Zealand, the last large land on Earth to be settled."),
       (1325, None, "islamic", "Ibn Battuta", "Thirty years of travel from Tangier to China, the widest account of the medieval Islamic world."),
       (1405, None, "china", "Zheng He's fleets", "The Ming treasure fleets sail to India, Arabia and East Africa, then stop."),
       (1488, None, "europe", "Round the Cape", "Dias rounds the southern tip of Africa; ten years later da Gama reaches India with a Gujarati pilot."),
       (1492, "columbus-1492", "europe", "Columbus", "Columbus crosses the Atlantic; Europe's map of the sea starts to grow faster than its map of the land."),
       (1520, None, "europe", "Magellan's Pacific", "Magellan's fleet crosses the Pacific, the largest single blank on the map."),
       (1770, None, "europe", "Cook", "Cook's three voyages chart New Zealand, eastern Australia and the high southern ocean, with Tupaia as navigator on the first."),
       (1805, "lewis-clark-1804", "europe", "Across North America", "Lewis and Clark cross to the Pacific, with Sacagawea and Shoshone and Nez Perce guides."),
       (1870, None, "europe", "Africa's interior", "The decades of fastest growth: Livingstone, Stanley, Barth and many others cross the African interior."),
       (1911, None, "europe", "The poles", "Amundsen and Scott reach the South Pole; flights soon cross the Arctic and Antarctica."),
       (1960, None, "europe", "1960", "Where the map stops. Every dark cell was known to the people who lived there.")]
ids = {e["id"] for e in J}
for m in MOM:
    assert m[1] is None or m[1] in ids, m
SITE["moments"] = [{"y": y, "id": j, "v": v, "t": t, "x": x} for y, j, v, t, x in MOM]

# places for search: Natural Earth populated places (capitals and larger towns) and countries
pp = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")["features"]
import h3
CI = {c: i for i, c in enumerate(G["cells"])}
def years_at(lat, lon):
    i = CI[h3.latlng_to_cell(lat, lon, H3_RES)]
    out = []
    for vp in VIEWPOINTS:
        f = int(S[vp]["first"][i]); b = int(S[vp]["by"][i])
        out += [f if f < NEVER else None, GI[str(S[vp]["ids"][b])] if b >= 0 else None]
    return out
PL = []
seen = set()
for f in sorted(pp, key=lambda f: (f["properties"]["scalerank"], -f["properties"]["pop_max"])):
    p = f["properties"]
    if not (p["scalerank"] <= 6 or p["adm0cap"] or p["pop_max"] >= 300000): continue
    key = (p["name"], p["adm0name"])
    if key in seen: continue
    seen.add(key)
    PL.append([p["name"], p["adm0name"], round(p["longitude"], 3), round(p["latitude"], 3), p["scalerank"]] + years_at(p["latitude"], p["longitude"]))
adm = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")["features"]
for f in adm:
    p = f["properties"]
    lon, lat = p.get("LABEL_X"), p.get("LABEL_Y")
    if lon is None: continue
    PL.append([p["NAME"], "country", round(lon, 3), round(lat, 3), -1] + years_at(lat, lon))
SITE["places"] = PL
SITE["labels"] = [[p[0], p[2], p[3]] for p in PL if 0 <= p[4] <= 1][:80]
jsave(SITE, f"{DATA}/site.json")
print("site.json", os.path.getsize(f"{DATA}/site.json") // 1024, "KB;", len(PL), "places")

# borders and coastlines (simplified)
def lines(feats, tol):
    out = []
    for f in feats:
        g = shape(f["geometry"]).simplify(tol, preserve_topology=True)
        polys = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
        for p in polys:
            for ring in [p.exterior] + list(p.interiors):
                c = np.round(np.array(ring.coords), 2)
                if len(c) >= 4:
                    out.append(c.ravel().tolist())
    return out
jsave(lines(adm, .08), f"{DATA}/borders.json")
land = jload(f"{GEO}/ne_50m_land.geojson")["features"] + jload(ICE)["features"]
jsave(lines(land, .05), f"{DATA}/coast.json")
for fn in ("borders.json", "coast.json"):
    print(fn, os.path.getsize(f"{DATA}/{fn}") // 1024, "KB")
