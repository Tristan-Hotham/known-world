"""Every number used anywhere (data/results.json), from the main run and the sensitivity runs of 03_reveal.py.

Definitions
  * known: a grid cell is known to a viewpoint in year t when a journey of that viewpoint has revealed it by t (reveal.py),
    or it lies in a small enclosed pocket filled from its rim, and it has not been lost again.
  * land share: area of known land cells over all land cells (Natural Earth 50m land plus Antarctic ice shelves).
    Earth's surface share: area of all known cells over the area of the Earth.
  * new area of a journey: the area of the cells it was the first (or the rim of a filled pocket was the first) to reveal.
  * country of a land cell: the Natural Earth country its centre falls in (Antarctica for ice shelves)."""
import pickle
from collections import Counter
from reveal import *

JALL = jload(f"{DATA}/expeditions.json")
JB = {e["id"]: e for e in JALL}
J = [e for e in JALL if e["layer"] == "journey"]          # the journeys; the survey and settlement layer is counted apart
R = {}
S = pickle.load(open(f"{WORK}/state_main.pkl", "rb"))
RUNS = ["main", "journeys_only", "radius_half", "radius_1p5", "no_fill", "fill_25", "fill_400", "confirmed_only", "no_base"]
ALL = {r: (S if r == "main" else pickle.load(open(f"{WORK}/state_{r}.pkl", "rb"))) for r in RUNS}
YRS = np.arange(YEAR0, YEAR1 + 1)
CN = G["cnames"]; COUNTRY = G["country"]
pc = lambda x: round(100 * float(x), 1)
km2 = lambda m: int(round(float(AREA[m].sum()), -3))

# ---------------- data ----------------
st = Counter(e["source_status"] for e in J)
R["data"] = {"journeys": len(J), "files": 8, "by_viewpoint": dict(Counter(e["viewpoint"] for e in J)),
             "by_mode": dict(Counter(e["mode"] for e in J)), "by_status": dict(st),
             "status_pct": {k: pc(st[k] / len(J)) for k in STATUS},
             "confirmed_n": sum(st[k] for k in CONFIRMED), "confirmed_pct": pc(sum(st[k] for k in CONFIRMED) / len(J)),
             "waypoints": sum(len(e["waypoints"]) for e in J),
             "earliest": min(e["start"] for e in J), "latest": max(e["end"] for e in J),
             "europe_earliest": min(e["start"] for e in J if e["viewpoint"] == "europe"),
             "lost_flagged": sum(1 for e in J if e["lost"]),
             "low_conf": sum(1 for e in J if e.get("route_confidence") == "low"),
             "with_guides": sum(1 for e in J if re.search(r"guide|interpreter|pilot|navigator", e["notes"] or "", re.I))}
R["data"]["europe_n"] = R["data"]["by_viewpoint"]["europe"]
SV = [e for e in JALL if e["layer"] == "survey"]
R["data"]["surveys"] = len(SV); R["data"]["survey_first"] = min(e["start"] for e in SV); R["data"]["survey_last"] = max(e["start"] for e in SV)
LOGM = jload(f"{DATA}/merge_log.json")
R["data"]["merged_duplicates"] = len(LOGM["merged_duplicates"]); R["data"]["renamed"] = len(LOGM["renamed"])
R["grid"] = {"res": H3_RES, "cells": int(NC), "land_cells": int(LAND.sum()), "mean_km2": round(float(AREA.mean())),
             "land_mkm2": round(float(AREA[LAND].sum()) / 1e6, 1), "earth_mkm2": round(float(AREA.sum()) / 1e6, 1),
             "fill_cells": FILL_CELLS, "fill_km2": int(round(FILL_CELLS * float(AREA.mean()), -3)), "fill_step": FILL_STEP,
             "radius": RADIUS_KM, "step_km": STEP_KM, "year0": YEAR0, "year1": YEAR1}

# ---------------- series and key years ----------------
SER = {vp: series(S[vp]) for vp in VIEWPOINTS}
union = {k: np.minimum.reduce([S[vp][k] for vp in VIEWPOINTS]) for k in ("first",)}
# union of viewpoints (no lost handling needed beyond Europe's, which is regained elsewhere): known to anyone
U = {"first": np.minimum.reduce([np.where((S[vp]["lost"] < NEVER) & (S[vp]["regained"] >= NEVER), NEVER, S[vp]["first"]) for vp in VIEWPOINTS]),
     "lost": np.full(NC, NEVER), "regained": np.full(NC, NEVER)}
SER["all"] = series(U)
KEY = [-1400, -1000, -500, -300, 1, 150, 500, 1000, 1200, 1400, 1492, 1500, 1550, 1600, 1650, 1700, 1750, 1800, 1850, 1900, 1930, 1960]
R["share"] = {vp: {str(y): {"land": pc(SER[vp]["land"][y - YEAR0]), "surface": pc(SER[vp]["surface"][y - YEAR0])} for y in KEY} for vp in SER}
R["series_decades"] = {vp: {"years": list(range(YEAR0, YEAR1 + 1, 10)) + ([YEAR1] if YEAR1 % 10 else []),
                            "land": [pc(SER[vp]["land"][y - YEAR0]) for y in range(YEAR0, YEAR1 + 1, 10)],
                            "surface": [pc(SER[vp]["surface"][y - YEAR0]) for y in range(YEAR0, YEAR1 + 1, 10)]} for vp in SER}
E = SER["europe"]


def milestones(ser):
    out = {}
    for q in (10, 25, 50, 75, 90):
        hit = np.where(ser >= q / 100)[0]
        out[str(q)] = int(YRS[hit[0]]) if len(hit) else None
    return out


R["milestones"] = {"land": milestones(E["land"]), "surface": milestones(E["surface"])}
# fastest decade (calendar decades 1400s to 1950s and before)
dec = {}
for d in range(-1400, 1960, 10):
    a, b = max(d, YEAR0) - YEAR0, min(d + 10, YEAR1) - YEAR0
    dec[d] = (E["land"][b] - E["land"][a], E["surface"][b] - E["surface"][a])
dl = max(dec, key=lambda d: dec[d][0]); ds = max(dec, key=lambda d: dec[d][1])
R["fastest"] = {"land_decade": dl, "land_gain": pc(dec[dl][0]), "surface_decade": ds, "surface_gain": pc(dec[ds][1]),
                "land_top5": [{"decade": d, "gain": pc(dec[d][0])} for d in sorted(dec, key=lambda d: -dec[d][0])[:5]]}
dm = max((d for d in dec if d >= 1400), key=lambda d: dec[d][0])
R["fastest"]["land_decade_after_1400"] = dm; R["fastest"]["land_gain_after_1400"] = pc(dec[dm][0])
cent = {}
for c0 in range(-1400, 1960, 100):
    a, b = max(c0, YEAR0) - YEAR0, min(c0 + 100, YEAR1) - YEAR0
    cent[c0] = pc(E["land"][b] - E["land"][a])
R["century_gain"] = {str(k): v for k, v in cent.items()}
R["fastest"]["land_century"] = max(cent, key=cent.get)
R["fastest"]["land_century_gain"] = cent[R["fastest"]["land_century"]]
# when Europe overtook the others (land and surface): first year after which Europe stays ahead for good
R["overtake"] = {}
for vp in ("islamic", "china", "polynesia"):
    o = {}
    for k in ("land", "surface"):
        behind = np.where(E[k] < SER[vp][k] - 1e-9)[0]
        o[k] = int(YRS[behind[-1] + 1]) if len(behind) else None
        o[k + "_other_ahead_from"] = int(YRS[behind[0]]) if len(behind) else None
    R["overtake"][vp] = o
behind = np.where(E["land"] < np.maximum.reduce([SER[v]["land"] for v in ("islamic", "china")]) - 1e-9)[0]
R["overtake"]["largest_other_land"] = int(YRS[behind[-1] + 1]) if len(behind) else None
for vp in VIEWPOINTS:
    R["share"][vp]["peak_land"] = pc(SER[vp]["land"].max()); R["share"][vp]["peak_surface"] = pc(SER[vp]["surface"].max())
    R["share"][vp]["final_year_growth"] = int(YRS[np.where(np.diff(SER[vp]["land"]) > 1e-6)[0][-1] + 1]) if (np.diff(SER[vp]["land"]) > 1e-6).any() else None

# ---------------- biggest journeys (Europe) ----------------
def new_area(vp):
    s = S[vp]; out = []
    ids = s["ids"]
    for msk, key in ((np.ones(NC, bool), "all"), (LAND, "land")):
        m = msk & (s["by"] >= 0)
        a = np.bincount(s["by"][m], weights=AREA[m], minlength=len(ids))
        out.append(a)
    rows = []
    for k, jid in enumerate(ids):
        e = JB[jid]
        rows.append({"id": jid, "leader": e["leader"], "label": e["label"], "start": e["start"], "end": e["end"], "mode": e["mode"],
                     "new_km2": int(round(out[0][k], -3)), "new_land_km2": int(round(out[1][k], -3))})
    return rows


NEW = {vp: new_area(vp) for vp in VIEWPOINTS}
eu = [r for r in NEW["europe"] if r["mode"] not in ("base", "survey")]
R["biggest"] = {"all": sorted(eu, key=lambda r: -r["new_km2"])[:10], "land": sorted(eu, key=lambda r: -r["new_land_km2"])[:10]}
R["biggest"]["top10_all_share"] = pc(sum(r["new_km2"] for r in R["biggest"]["all"]) / float(AREA[S["europe"]["first"] < NEVER].sum()))
# ---------------- last areas lit (Europe) by country ----------------
cty = []
s = S["europe"]
for ci in np.unique(COUNTRY[LAND]):
    m = LAND & (COUNTRY == ci)
    tot = AREA[m].sum()
    if tot < 150000: continue
    yrs_ = np.where(s["first"][m] < NEVER, s["first"][m], NEVER)
    o = np.argsort(yrs_); cum = np.cumsum(AREA[m][o]) / tot
    y50 = yrs_[o][np.searchsorted(cum, .5)] if cum[-1] >= .5 else None
    y90 = yrs_[o][np.searchsorted(cum, .9)] if cum[-1] >= .9 else None
    known60 = AREA[m][known_at(s, YEAR1)[m]].sum() / tot
    first_any = int(yrs_.min()) if yrs_.min() < NEVER else None
    cty.append({"country": str(CN[ci]), "area_km2": int(round(tot, -3)), "first": first_any, "y50": int(y50) if y50 is not None and y50 < NEVER else None,
                "y90": int(y90) if y90 is not None and y90 < NEVER else None, "known_1960_pct": pc(known60)})
cty.sort(key=lambda r: -r["area_km2"])
R["countries"] = cty
CB = {r["country"]: r for r in cty}
late = sorted([r for r in cty if r["y50"] is not None], key=lambda r: -r["y50"])
R["last_lit"] = {"by_half": late[:10],
                 "least_known_1960": sorted(cty, key=lambda r: r["known_1960_pct"])[:10],
                 "unknown_land_1960_mkm2": round(float(AREA[LAND & ~known_at(s, YEAR1)].sum()) / 1e6, 1),
                 "unknown_antarctica_mkm2": round(float(AREA[LAND & ~known_at(s, YEAR1) & (CN[COUNTRY] == "Antarctica")].sum()) / 1e6, 1)}
lit_late = LAND & (s["first"] >= 1900) & (s["first"] < NEVER)
R["last_lit"]["after_1900_mkm2"] = round(float(AREA[lit_late].sum()) / 1e6, 1)
lc = Counter()
for i in np.where(lit_late)[0]: lc[str(CN[COUNTRY[i]])] += AREA[i]
R["last_lit"]["after_1900_top"] = [{"country": k, "km2": int(round(v, -3))} for k, v in lc.most_common(6)]

# ---------------- known to others before Europe ----------------
R["before_europe"] = {}
fe = S["europe"]["first"]
for vp in ("islamic", "china", "polynesia"):
    f = S[vp]["first"]
    ahead = (f < NEVER) & (f < fe)
    lag = np.where(fe[ahead] < NEVER, fe[ahead] - f[ahead], np.nan)
    w = AREA[ahead]
    ok = ~np.isnan(lag)
    o = np.argsort(lag[ok]); cw = np.cumsum(w[ok][o]) / w[ok].sum()
    med = float(lag[ok][o][np.searchsorted(cw, .5)]) if ok.any() else None
    c = Counter()
    for i in np.where(ahead & LAND)[0]: c[str(CN[COUNTRY[i]])] += AREA[i]
    R["before_europe"][vp] = {"km2": km2(ahead), "land_km2": km2(ahead & LAND), "sea_km2": km2(ahead & ~LAND),
                              "known_km2_1960": km2(known_at(S[vp], YEAR1)),
                              "pct_of_own": pc(AREA[ahead].sum() / AREA[f < NEVER].sum()),
                              "median_lead_years": int(round(med)) if med is not None else None,
                              "top_countries": [{"country": k, "km2": int(round(v, -3))} for k, v in c.most_common(6)]}


def region_first(lat0, lat1, lon0, lon1, land_only=True):
    m = (LAT >= lat0) & (LAT <= lat1) & (LON >= lon0) & (LON <= lon1)
    if land_only: m &= LAND
    out = {}
    for vp in VIEWPOINTS:
        f = S[vp]["first"][m]
        out[vp] = int(np.median(np.where(f < NEVER, f, NEVER))) if len(f) else None
        out[vp] = None if out[vp] is None or out[vp] >= NEVER else out[vp]
        out[vp + "_earliest"] = int(f.min()) if len(f) and f.min() < NEVER else None
    out["cells"] = int(m.sum())
    return out


R["regions"] = {"hawaii": region_first(18.5, 22.5, -160.5, -154.5), "new_zealand": region_first(-47.5, -34, 166, 179),
                "rapa_nui": region_first(-27.5, -26.8, -109.6, -109.1, land_only=False), "madagascar": region_first(-26, -12, 43, 51),
                "iceland": region_first(63, 66.7, -24.5, -13.3), "java": region_first(-8.8, -5.8, 105, 114.6),
                "japan": region_first(31, 41.5, 129.5, 142), "tibet": region_first(28, 36, 80, 96),
                "mali_niger": region_first(12, 18, -5, 3), "zanzibar_coast": region_first(-8, -3, 38.5, 40, land_only=False),
                "australia": region_first(-39, -11, 113, 154), "greenland": region_first(60, 83, -73, -12)}

# ---------------- sensitivity ----------------
SENS = {}
for r in RUNS:
    SS = ALL[r]
    se = series(SS["europe"])
    o = {"land": {str(y): pc(se["land"][y - YEAR0]) for y in (150, 1492, 1700, 1800, 1900, 1960)},
         "surface": {str(y): pc(se["surface"][y - YEAR0]) for y in (1492, 1800, 1960)},
         "milestones": milestones(se["land"])}
    for vp in ("islamic", "china"):
        sv = series(SS[vp])
        behind = np.where(se["land"] < sv["land"] - 1e-9)[0]
        o["overtake_" + vp] = int(YRS[behind[-1] + 1]) if len(behind) else None
    dec_ = {d: se["land"][min(d + 10, YEAR1) - YEAR0] - se["land"][max(d, YEAR0) - YEAR0] for d in range(-1400, 1960, 10)}
    o["fastest_decade"] = max(dec_, key=dec_.get)
    o["journeys"] = int(sum(len(SS[vp]["ids"]) for vp in VIEWPOINTS))
    SENS[r] = o
R["sensitivity"] = SENS
R["sens_range"] = {"land_1960_min": min(v["land"]["1960"] for v in SENS.values()), "land_1960_max": max(v["land"]["1960"] for v in SENS.values()),
                   "land_1800_min": min(v["land"]["1800"] for v in SENS.values()), "land_1800_max": max(v["land"]["1800"] for v in SENS.values())}
R["filled_km2"] = {vp: km2(S[vp]["filled"]) for vp in VIEWPOINTS}
R["filled_pct_of_known_europe"] = pc(AREA[S["europe"]["filled"]].sum() / AREA[S["europe"]["first"] < NEVER].sum())
R["meta"] = {"page": PAGE, "repo": REPO, "slug": SLUG}

# ---------------- journeys only (no survey and settlement layer) ----------------
SJ = ALL["journeys_only"]["europe"]; sj = series(SJ)
R["journeys_only"] = {"share": {str(y): {"land": pc(sj["land"][y - YEAR0]), "surface": pc(sj["surface"][y - YEAR0])} for y in KEY},
                      "milestones": {"land": milestones(sj["land"]), "surface": milestones(sj["surface"])},
                      "unknown_land_1960_mkm2": round(float(AREA[LAND & ~known_at(SJ, YEAR1)].sum()) / 1e6, 1)}
R["survey_added_1960"] = pc(E["land"][-1] - sj["land"][-1])
R["survey_first_by_km2"] = km2((S["europe"]["by"] >= 0) & np.isin(S["europe"]["ids"][np.maximum(S["europe"]["by"], 0)], [e["id"] for e in SV]) & LAND)
SERJ = sj

# ---------------- checks ----------------
m = R["milestones"]["land"]
assert m["10"] < m["25"] <= (m["50"] or 9999)
assert all(np.all(np.diff(SER[vp]["land"]) >= -0.01) for vp in VIEWPOINTS)   # only small losses (lost knowledge)
assert R["share"]["europe"]["1960"]["land"] > R["share"]["europe"]["1492"]["land"] > R["share"]["europe"]["150"]["land"]
print("OVERTAKE", R["overtake"])
assert R["before_europe"]["polynesia"]["km2"] > 0 and R["regions"]["new_zealand"]["polynesia"] < R["regions"]["new_zealand"]["europe"]
assert R["regions"]["hawaii"]["polynesia"] < R["regions"]["hawaii"]["europe"]
assert S["europe"]["multi_gap"] == 0
assert abs(sum(R["data"]["status_pct"].values()) - 100) < .5
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("milestones", "fastest", "overtake", "last_lit", "sens_range", "filled_pct_of_known_europe")}, indent=0)[:4000])
print(json.dumps(R["share"]["europe"])[:900])
print([(r["label"], r["start"], r["new_km2"]) for r in R["biggest"]["all"]])
print([(r["label"], r["start"], r["new_land_km2"]) for r in R["biggest"]["land"]])
print(json.dumps(R["before_europe"])[:1500])
print(json.dumps(R["regions"])[:1500])
print(json.dumps(SENS, indent=0)[:3000])
print(R["data"])
