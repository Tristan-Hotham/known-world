"""Merge the regional gazetteer files into one clean set of journeys.

Reads EXPED/*.json and VERIF; writes data/expeditions.json (one object per journey, with source_status),
data/expeditions.csv (one row per journey), data/routes.geojson (routes split at the 180 degree meridian) and
data/merge_log.json (every fix, rename and drop).

Source status (one per journey):
  years_confirmed      the automatic check found the start and end years in the cited Wikipedia article
  years_not_confirmed  the check found the article but not one or both years, or the compiler's notes say the dates
                       (not the whole route) came from general knowledge, or only part of the sources could be read
  unsourced            the cited article could not be found by the check, or the compiler's notes say the cited page could
                       not be read and route and dates came from general knowledge
  read_by_compiler     not in the check; the compiling agent took route and dates from the pages it cites
"""
import glob, csv
from common import *

LOG = {"fixed": [], "dropped_points": [], "renamed": [], "merged_duplicates": [], "dropped": [], "sources_replaced": []}

# rome-medieval cites a mirror site for four entries: use the matching English Wikipedia pages instead
CAVAC = {
    "papar-iceland-795": ["https://en.wikipedia.org/wiki/Papar", "https://en.wikipedia.org/wiki/Dicuil", "https://en.wikipedia.org/wiki/Settlement_of_Iceland"],
    "naddodd-860": ["https://en.wikipedia.org/wiki/Naddodd", "https://en.wikipedia.org/wiki/Settlement_of_Iceland"],
    "gardar-860": ["https://en.wikipedia.org/wiki/Gar%C3%B0ar_Svavarsson", "https://en.wikipedia.org/wiki/Settlement_of_Iceland"],
    "floki-868": ["https://en.wikipedia.org/wiki/Hrafna-Fl%C3%B3ki_Vilger%C3%B0arson", "https://en.wikipedia.org/wiki/Settlement_of_Iceland"],
}
# Entries outside the automatic check whose notes say part of the sources could not be read but another cited page
# was: their dates are not fully confirmed rather than unsourced.
PARTIAL = {"magellan-1520", "base-homeric-world", "ptolemy-geography-150", "ohthere-890-north", "loaisa-1526"}

NOTREAD = re.compile(r"could not be fetched|not fetched|were blocked|access blocked|fetch blocked", re.I)
GENDATES = re.compile(r"(dates?|route and dates)[^.]*from (the compiler's )?general knowledge|from general knowledge", re.I)


def status(e, V):
    v = V.get(e["id"])
    if v:
        if v["date_check"] == "years_confirmed": return "years_confirmed"
        if v["date_check"] == "article_missing": return "unsourced"
        return "years_not_confirmed"
    n = e.get("notes") or ""
    if not e["sources"]:
        return "unsourced"
    if e["id"] in PARTIAL or e["id"] in CAVAC:
        return "years_not_confirmed"
    if NOTREAD.search(n):
        return "unsourced"
    if GENDATES.search(n):
        return "years_not_confirmed"
    return "read_by_compiler"


def clean_text(s):
    if s is None: return None
    s = dash(str(s)).strip()
    return re.sub(r"\s+", " ", s)


def fix_points(e):
    """Normalise waypoints: [lon, lat, year], latitudes in range, longitudes in -180..180, years non-decreasing,
    lone spikes (a point far off a line its neighbours almost join) removed."""
    wp = []
    for i, p in enumerate(e["waypoints"]):
        lon, lat = float(p[0]), float(p[1])
        y = int(round(p[2])) if len(p) > 2 and p[2] is not None else None
        if abs(lat) > 90 and abs(lon) <= 90:
            LOG["fixed"].append(f"{e['id']}: point {i} lon/lat swapped"); lon, lat = lat, lon
        if abs(lat) > 90:
            LOG["dropped_points"].append(f"{e['id']}: point {i} latitude {lat} out of range"); continue
        lon = ((lon + 180) % 360) - 180 if abs(lon) > 180 else lon
        wp.append([round(lon, 4), round(lat, 4), y])
    # years: fill missing by interpolation between known ones, clip to start..end, make non-decreasing
    ys = [p[2] for p in wp]
    known = [i for i, y in enumerate(ys) if y is not None]
    if not known:
        for p in wp: p[2] = e["start"]
    else:
        for i, p in enumerate(wp):
            if p[2] is None:
                p[2] = int(round(np.interp(i, known, [ys[k] for k in known])))
    lo, hi = e["start"], e["end"]
    for i, p in enumerate(wp):
        if p[2] < lo or p[2] > hi:
            LOG["fixed"].append(f"{e['id']}: point {i} year {p[2]} clipped to {lo} to {hi}")
            p[2] = min(max(p[2], lo), hi)
        if i and p[2] < wp[i - 1][2]:
            LOG["fixed"].append(f"{e['id']}: point {i} year {p[2]} raised to {wp[i - 1][2]} (years must not go back)")
            p[2] = wp[i - 1][2]
    # spikes: a single point more than 1,500 km off the line its neighbours almost join (a slip of sign or digit)
    if e["mode"] != "base" and len(wp) >= 3:
        keep = [True] * len(wp)
        for i in range(1, len(wp) - 1):
            a, b, c = wp[i - 1], wp[i], wp[i + 1]
            ab = gc_km(a[1], a[0], b[1], b[0]); bc = gc_km(b[1], b[0], c[1], c[0]); ac = gc_km(a[1], a[0], c[1], c[0])
            if ab > 1500 and bc > 1500 and ab + bc > 3 * ac + 2500:
                keep[i] = False
                LOG["dropped_points"].append(f"{e['id']}: point {i} {b[:2]} is a spike ({ab:.0f} km out and {bc:.0f} km back, neighbours {ac:.0f} km apart)")
        wp = [p for p, k in zip(wp, keep) if k]
    return wp


def main():
    V = jload(VERIF)
    files = sorted(glob.glob(os.path.join(EXPED, "*.json")))
    rows = []
    for f in files:
        reg = os.path.basename(f)[:-5]
        for e in jload(f):
            e = dict(e); e["region"] = reg; e["_orig"] = e["id"]
            rows.append(e)
    print(len(files), "files", len(rows), "entries")
    out, seen = [], {}
    for e in rows:
        e["viewpoint"] = e.get("viewpoint") or "europe"
        assert e["viewpoint"] in VIEWPOINTS, e["id"]
        assert e["mode"] in RADIUS_KM, (e["id"], e["mode"])
        e["start"] = int(e["start"]); e["end"] = int(e["end"] if e.get("end") is not None else e["start"])
        if e["end"] < e["start"]:
            LOG["fixed"].append(f"{e['id']}: end {e['end']} before start {e['start']}, swapped"); e["start"], e["end"] = e["end"], e["start"]
        if not (YEAR0 <= e["start"] <= YEAR1):
            LOG["dropped"].append(f"{e['id']}: start {e['start']} outside {YEAR0} to {YEAR1}"); continue
        e["end"] = min(e["end"], YEAR1)
        e["waypoints"] = fix_points(e)
        if len(e["waypoints"]) < 1:
            LOG["dropped"].append(f"{e['id']}: no usable waypoints"); continue
        for k in ("leader", "label", "sponsor", "summary", "notes"):
            e[k] = clean_text(e.get(k))
        e["sources"] = [s for s in (e.get("sources") or []) if s]
        if e["id"] in CAVAC:
            old = e["sources"]; e["sources"] = CAVAC[e["id"]]
            LOG["sources_replaced"].append(f"{e['id']}: citation of a mirror site replaced by {e['sources']} (English Wikipedia)")
            e["notes"] = (e["notes"] or "").replace("Shetland stop from Landnamabok tradition; the source used mentions the Faroes only.", "Shetland and Faroe stops from the Landnamabok tradition.")
            e["notes"] = (e["notes"] + " Citation replaced with the English Wikipedia pages; dates not rechecked against them.").strip()
        assert not any("cavac" in s for s in e["sources"]), e["id"]
        e["lost"] = int(e["lost"]) if e.get("lost") not in (None, "") else None
        e["regained"] = e.get("regained") or None
        # duplicates across regional files
        if e["id"] in seen:
            o = seen[e["id"]]
            same = (o["start"] == e["start"] and o["mode"] == e["mode"] and
                    gc_km(o["waypoints"][0][1], o["waypoints"][0][0], e["waypoints"][0][1], e["waypoints"][0][0]) < 300 and
                    gc_km(o["waypoints"][-1][1], o["waypoints"][-1][0], e["waypoints"][-1][1], e["waypoints"][-1][0]) < 300)
            if same:
                keep, drop = (o, e) if len(o["waypoints"]) >= len(e["waypoints"]) else (e, o)
                LOG["merged_duplicates"].append(f"{e['id']}: in {o['region']} and {e['region']}, same journey; kept the {keep['region']} version ({len(keep['waypoints'])} points)")
                if keep is e:
                    out[out.index(o)] = e; seen[e["id"]] = e
                continue
            new = f"{e['id']}-{e['region'].split('-')[0]}"
            LOG["renamed"].append(f"{e['id']}: also in {o['region']} as a different journey; {e['region']} version renamed {new}")
            e["id"] = new
        seen[e["id"]] = e
        out.append(e)
    # the survey and settlement layer (code/surveys.py)
    from surveys import SURVEYS
    a1 = {f["properties"]["iso_3166_2"]: (f["properties"]["longitude"], f["properties"]["latitude"]) for f in jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")["features"]}
    a0 = {f["properties"]["ADM0_A3"]: (f["properties"]["LABEL_X"], f["properties"]["LABEL_Y"]) for f in jload(f"{GEO}/ne_50m_admin_0_countries.geojson")["features"]}
    for sv in SURVEYS:
        if sv.get("bbox"):
            b_ = sv["bbox"]; lab = ((b_[0] + b_[2]) / 2, (b_[1] + b_[3]) / 2)
        else:
            pts_ = [a1[c] for c in sv.get("iso", []) if c in a1] + [a0[c] for c in sv.get("a3", []) if c in a0]
            assert pts_, sv["id"]
            lab = (float(np.mean([p[0] for p in pts_])), float(np.mean([p[1] for p in pts_])))
        missing = [c for c in sv.get("iso", []) if c not in a1] + [c for c in sv.get("a3", []) if c not in a0]
        if missing: LOG["fixed"].append(f"{sv['id']}: codes not in Natural Earth: {missing}")
        out.append({"id": sv["id"], "_orig": sv["id"], "viewpoint": "europe", "layer": "survey", "leader": sv["leader"], "label": sv["label"], "sponsor": sv["sponsor"],
                    "start": sv["year"], "end": sv["year"], "mode": "survey", "route_confidence": "medium", "lost": None, "regained": None,
                    "summary": sv["summary"], "sources": sv["src"], "region": "survey-layer",
                    "notes": "Survey and settlement layer: the region lights in this year. Date from general knowledge; the cited pages were not read for this layer.",
                    "areas": {"iso": sv.get("iso", []), "a3": sv.get("a3", []), "bbox": sv.get("bbox")},
                    "waypoints": [[round(lab[0], 3), round(lab[1], 3), sv["year"]]]})
    for e in out:
        e.setdefault("layer", "journey")
    # source status and checked URLs
    for e in out:
        v = V.get(e["_orig"])
        e["source_status"] = "years_not_confirmed" if e["layer"] == "survey" else status(dict(e, id=e["_orig"]), V)
        if v and v.get("url") and e["source_status"] != "unsourced":
            if not e["sources"] or e["sources"][0] != v["url"]:
                LOG["sources_replaced"].append(f"{e['id']}: first source {e['sources'][:1]} -> {v['url']} (checked article)")
            e["sources"] = [v["url"]] + [s for s in e["sources"][1:] if s != v["url"]]
        e["date_check"] = v["date_check"] if v else None
    for e in out:
        if e["regained"] and e["regained"] not in seen:
            LOG["fixed"].append(f"{e['id']}: regained by unknown id {e['regained']}, kept as text");
    out.sort(key=lambda e: (e["start"], e["id"]))
    ids = [e["id"] for e in out]
    assert len(ids) == len(set(ids))
    keys = ["id", "viewpoint", "layer", "leader", "label", "sponsor", "start", "end", "mode", "route_confidence", "source_status", "date_check",
            "lost", "regained", "summary", "notes", "sources", "region", "areas", "waypoints"]
    clean = [{k: e.get(k) for k in keys} for e in out]
    for e in clean:
        for k in ("leader", "label", "summary", "notes"):
            assert not e[k] or ("—" not in e[k] and "–" not in e[k] and "--" not in e[k]), (e["id"], k)
    jsave(clean, f"{DATA}/expeditions.json")
    with open(f"{DATA}/expeditions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([k for k in keys if k not in ("waypoints", "areas")] + ["n_waypoints", "first_lon", "first_lat", "last_lon", "last_lat"])
        for e in clean:
            w.writerow([" | ".join(e[k]) if k == "sources" else e[k] for k in keys if k not in ("waypoints", "areas")] +
                       [len(e["waypoints"]), *e["waypoints"][0][:2], *e["waypoints"][-1][:2]])
    feats = []
    for e in clean:
        xs = unwrap([p[0] for p in e["waypoints"]])
        line = [[x, p[1]] for x, p in zip(xs, e["waypoints"])]
        parts = split_antimeridian(line) if len(line) > 1 else [[line[0], line[0]]]
        if e["layer"] == "survey": continue
        feats.append({"type": "Feature", "properties": {k: e[k] for k in keys if k not in ("waypoints", "notes", "areas")},
                      "geometry": {"type": "MultiLineString", "coordinates": [[[round(x, 4), round(y, 4)] for x, y in p] for p in parts]}})
    jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/routes.geojson")
    from collections import Counter
    LOG["counts"] = {"files": [os.path.basename(f) for f in files], "entries_read": len(rows), "journeys": len(clean),
                     "by_viewpoint": Counter(e["viewpoint"] for e in clean), "by_status": Counter(e["source_status"] for e in clean),
                     "by_mode": Counter(e["mode"] for e in clean), "by_layer": Counter(e["layer"] for e in clean)}
    jsave(LOG, f"{DATA}/merge_log.json", indent=1)
    print(json.dumps(LOG["counts"], indent=0))
    for k in ("fixed", "dropped_points", "renamed", "merged_duplicates", "dropped"):
        print(k, len(LOG[k]), LOG[k][:8])


if __name__ == "__main__":
    main()
