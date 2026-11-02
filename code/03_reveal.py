"""Run the reveal model: the main run for each viewpoint and the sensitivity runs (radii halved and increased by half,
no pocket fill, smaller and larger fills, confirmed-only journeys, no starting worlds).
Writes WORK/cov_<mult>.npz (per-journey coverage), WORK/state_<run>.npz (per-cell results for each viewpoint) and
data/cells.csv.gz (the main run, one row per grid cell)."""
import time, csv, gzip, pickle
from reveal import *

J = jload(f"{DATA}/expeditions.json")
RUNS = {
    "main": dict(mult=1.0, fill=FILL_CELLS, keep=lambda e: True),
    "radius_half": dict(mult=0.5, fill=FILL_CELLS, keep=lambda e: True),
    "radius_1p5": dict(mult=1.5, fill=FILL_CELLS, keep=lambda e: True),
    "no_fill": dict(mult=1.0, fill=0, keep=lambda e: True),
    "fill_25": dict(mult=1.0, fill=25, keep=lambda e: True),
    "fill_400": dict(mult=1.0, fill=400, keep=lambda e: True),
    "confirmed_only": dict(mult=1.0, fill=FILL_CELLS, keep=lambda e: e["source_status"] in CONFIRMED),
    "no_base": dict(mult=1.0, fill=FILL_CELLS, keep=lambda e: e["mode"] != "base"),
    "journeys_only": dict(mult=1.0, fill=FILL_CELLS, keep=lambda e: e["layer"] == "journey"),
}


def run(name, cfg, covs):
    t0 = time.time()
    if cfg["mult"] not in covs:
        covs[cfg["mult"]] = coverage(J, cfg["mult"])
    cov = covs[cfg["mult"]]
    out = {}
    for vp in VIEWPOINTS:
        JV = [e for e in J if e["viewpoint"] == vp and cfg["keep"](e)]
        st = combine(JV, cov, cfg["fill"])
        st["ids"] = np.array([e["id"] for e in JV])
        out[vp] = st
        print(f"  {name} {vp}: {len(JV)} journeys, {int((st['first'] < NEVER).sum())} cells known by {YEAR1}, filled {int(st['filled'].sum())}, multi-gap {st['multi_gap']}")
    with open(f"{WORK}/state_{name}.pkl", "wb") as f:
        pickle.dump(out, f)
    print(name, round(time.time() - t0, 1), "s")
    return out


if __name__ == "__main__":
    import sys
    covs = {}
    t0 = time.time()
    covs[1.0] = coverage(J, 1.0)
    with open(f"{WORK}/cov_1.0.pkl", "wb") as f:
        pickle.dump(covs[1.0], f)
    print("coverage", round(time.time() - t0, 1), "s")
    names = sys.argv[1:] or list(RUNS)
    for n in names:
        S = run(n, RUNS[n], covs)
        if n == "main":
            with gzip.open(f"{DATA}/cells.csv.gz", "wt", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["h3", "lat", "lon", "area_km2", "land"] + [f"{vp}_{k}" for vp in VIEWPOINTS for k in ("first_year", "first_by", "filled", "lost_year", "regained_year")])
                cells = G["cells"]
                cols = []
                for vp in VIEWPOINTS:
                    st = S[vp]
                    nv = lambda a: np.where(a < NEVER, a, -99999)
                    cols += [nv(st["first"]), np.where(st["by"] >= 0, st["ids"][np.maximum(st["by"], 0)], ""), st["filled"].astype(int), nv(st["lost"]), nv(st["regained"])]
                for i in range(NC):
                    row = [cells[i], round(float(LAT[i]), 4), round(float(LON[i]), 4), round(float(AREA[i]), 1), int(LAND[i])]
                    for c in cols:
                        v = c[i]
                        row.append("" if (isinstance(v, (int, np.integer)) and v == -99999) else v)
                    w.writerow(row)
            print("cells.csv.gz", os.path.getsize(f"{DATA}/cells.csv.gz") // 1024, "KB")
