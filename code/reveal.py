"""The reveal model, shared by 03_reveal.py (main run and sensitivity runs) and the figures.

coverage(J, mult): for every journey, the grid cells it reveals and the year each is revealed. Routes are densified to a
  point every STEP_KM km with years interpolated between dated waypoints; a cell is revealed when its centre lies within the
  mode's radius (RADIUS_KM, by sea or land cell, times mult) of a route point, in the year of the nearest such point.
  Starting-world entries (mode base) are a cloud of points, not a line, and are not joined up.
combine(...): per viewpoint, each cell's first year, the journey that first revealed it, enclosed-pocket fill, and
  the years it was lost and regained (a journey flagged lost stops counting from that year; the cell stays known if any
  other journey covers it)."""
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.neighbors import BallTree
from common import *

NEVER = 32000
G = np.load(f"{WORK}/grid.npz")
LAT, LON, AREA, LAND, NB = G["lat"], G["lon"], G["area"], G["land"], G["nb"]
ISO, A3 = G["iso"], G["a3"]
NC = len(LAT)
TREE = None


def tree():
    global TREE
    if TREE is None:
        TREE = BallTree(np.radians(np.c_[LAT, LON]), metric="haversine")
    return TREE


def densify(e):
    wp = e["waypoints"]
    xs = unwrap([p[0] for p in wp]); ys = [p[1] for p in wp]; ts = [p[2] for p in wp]
    if e["mode"] == "base" or len(wp) == 1:
        return np.array(ys), np.array(xs), np.array(ts, float)
    la, lo, yr_ = [ys[0]], [xs[0]], [ts[0]]
    for i in range(1, len(wp)):
        d = gc_km(ys[i - 1], xs[i - 1], ys[i], xs[i])
        n = max(1, int(np.ceil(d / STEP_KM)))
        f = np.arange(1, n + 1) / n
        la += list(ys[i - 1] + f * (ys[i] - ys[i - 1])); lo += list(xs[i - 1] + f * (xs[i] - xs[i - 1])); yr_ += list(ts[i - 1] + f * (ts[i] - ts[i - 1]))
    return np.array(la), np.array(lo), np.array(yr_)


def coverage(J, mult=1.0):
    """{journey id: (cell indices, years)}"""
    out = {}
    T = tree()
    for e in J:
        if e["mode"] == "survey":
            A = e["areas"]
            m = LAND & (np.isin(ISO, A["iso"]) | np.isin(A3, A["a3"]))
            if A.get("bbox"):
                b0 = A["bbox"]; m &= (LON >= b0[0]) & (LAT >= b0[1]) & (LON <= b0[2]) & (LAT <= b0[3])
            c = np.where(m)[0].astype(np.int32)
            out[e["id"]] = (c, np.full(len(c), e["start"], np.int32)); continue
        la, lo, ts = densify(e)
        lo = ((lo + 180) % 360) - 180
        rs, rl = RADIUS_KM[e["mode"]]["sea"] * mult, RADIUS_KM[e["mode"]]["land"] * mult
        ind, dist = T.query_radius(np.radians(np.c_[la, lo]), r=max(rs, rl) / 6371.0, return_distance=True)
        cnt = np.array([len(i) for i in ind])
        if cnt.sum() == 0:
            out[e["id"]] = (np.zeros(0, np.int32), np.zeros(0, np.int32)); continue
        c = np.concatenate(ind).astype(np.int32); d = np.concatenate(dist) * 6371.0
        y = np.repeat(ts, cnt)
        ok = d <= np.where(LAND[c], rl, rs)
        c, d, y = c[ok], d[ok], y[ok]
        o = np.lexsort((d, c))
        c, y = c[o], y[o]
        first = np.r_[True, c[1:] != c[:-1]]
        out[e["id"]] = (c[first], np.round(y[first]).astype(np.int32))
    return out


def adjacency():
    rows = np.repeat(np.arange(NC), 6); cols = NB.ravel()
    ok = cols >= 0
    return csr_matrix((np.ones(ok.sum(), np.int8), (rows[ok], cols[ok])), shape=(NC, NC))


ADJ = None


def combine(J, cov, fill_n=FILL_CELLS, fill_step=FILL_STEP):
    """J: the journeys of one viewpoint. Returns dict of per-cell arrays."""
    global ADJ
    first = np.full(NC, NEVER, np.int32); by = np.full(NC, -1, np.int32)
    perm_first = np.full(NC, NEVER, np.int32)          # earliest year from journeys never lost
    lost_iv = {}                                        # cell -> list of (start, end) from journeys flagged lost
    for k, e in enumerate(J):
        c, y = cov[e["id"]]
        if not len(c): continue
        better = y < first[c]
        first[c[better]] = y[better]; by[c[better]] = k
        if e.get("lost"):
            for ci, yi in zip(c, y):
                if yi < e["lost"]:
                    lost_iv.setdefault(int(ci), []).append((int(yi), int(e["lost"])))
        else:
            np.minimum.at(perm_first, c, y)
    # lost and regained: union of [start, lost) from lost journeys and [start, inf) from the others
    lost = np.full(NC, NEVER, np.int32); regained = np.full(NC, NEVER, np.int32)
    multi = 0
    for ci, iv in lost_iv.items():
        ivs = sorted(iv + ([(int(perm_first[ci]), NEVER)] if perm_first[ci] < NEVER else []))
        merged = []
        for a, b in ivs:
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        if merged[0][1] < NEVER:
            lost[ci] = merged[0][1]
            if len(merged) > 1:
                regained[ci] = merged[1][0]
                if len(merged) > 2 or merged[1][1] < NEVER:
                    multi += 1
    # enclosed pockets: checked every fill_step years; a pocket of unknown cells smaller than fill_n, wholly enclosed by
    # known cells, counts as known from the year its last rim cell became known
    filled = np.zeros(NC, bool)
    if fill_n:
        if ADJ is None: ADJ = adjacency()
        known_years = np.unique(first[first < NEVER])
        if len(known_years):
            for t in range(int(known_years[0]), YEAR1 + fill_step, fill_step):
                t = min(t, YEAR1)
                unk = first > t
                idx = np.where(unk)[0]
                sub = ADJ[idx][:, idx]
                ncomp, lab = connected_components(sub, directed=False)
                size = np.bincount(lab, minlength=ncomp)
                small = np.where(size < fill_n)[0]
                if not len(small): continue
                sel = np.isin(lab, small)
                cells_ = idx[sel]; labs = lab[sel]
                for comp in np.unique(labs):
                    cc = cells_[labs == comp]
                    rim = np.setdiff1d(NB[cc].ravel(), np.r_[cc, -1])
                    rim = rim[first[rim] <= t]
                    if not len(rim): continue
                    j = rim[np.argmax(first[rim])]
                    first[cc] = first[j]; by[cc] = by[j]; filled[cc] = True
    return {"first": first, "by": by, "filled": filled, "lost": lost, "regained": regained, "multi_gap": multi}


def known_at(st, t):
    return (st["first"] <= t) & ~((st["lost"] <= t) & (t < st["regained"]))


def series(st, years=None):
    """Area known by year: land and whole surface, as shares (0..1) of the land and the Earth."""
    yrs = np.arange(YEAR0, YEAR1 + 1) if years is None else np.asarray(years)
    out = {}
    for key, msk in (("land", LAND), ("surface", np.ones(NC, bool))):
        tot = AREA[msk].sum()
        diff = np.zeros(YEAR1 - YEAR0 + 3)
        def add(ys, w, sign):
            ys = np.clip(ys, YEAR0, YEAR1 + 1) - YEAR0
            np.add.at(diff, ys, sign * w)
        m = msk & (st["first"] < NEVER)
        add(st["first"][m], AREA[m], 1)
        m2 = msk & (st["lost"] < NEVER)
        add(st["lost"][m2], AREA[m2], -1)
        m3 = m2 & (st["regained"] < NEVER)
        add(st["regained"][m3], AREA[m3], 1)
        cum = np.cumsum(diff)[:YEAR1 - YEAR0 + 1] / tot
        out[key] = cum[yrs - YEAR0]
    return out
