"""The equal-area grid: every H3 cell at resolution H3_RES, with its centre, area, land or sea (centre on Natural Earth
50m land), modern country (for naming regions) and its six neighbours. Also the pixel-to-cell lookups for the page
raster (Web Mercator, RASTER x RASTER) and the video and figure raster (plate carree, VIDEO_W x VIDEO_W/2), with a
land mask at pixel level drawn from the same Natural Earth land.
Antarctic ice shelves (Natural Earth) count as land throughout: a cell on an ice shelf is a land cell.
Writes WORK/grid.npz, WORK/pix_merc.npz, WORK/pix_pc.npz."""
import h3, time
import shapely
from shapely.geometry import shape
from rasterio import features
from rasterio.transform import from_bounds
from common import *

t0 = time.time()
cells = sorted(c for r0 in h3.get_res0_cells() for c in h3.cell_to_children(r0, H3_RES))
N = len(cells)
idx = {c: i for i, c in enumerate(cells)}
ll = np.array([h3.cell_to_latlng(c) for c in cells])
area = np.array([h3.cell_area(c, "km^2") for c in cells])
nb = np.full((N, 6), -1, dtype=np.int32)
for i, c in enumerate(cells):
    ring = [idx[x] for x in h3.grid_ring(c, 1)]
    nb[i, :len(ring)] = ring
print(N, "cells", round(area.sum()), "km2", round(time.time() - t0, 1), "s")

land = jload(f"{GEO}/ne_50m_land.geojson")
LP = [shape(f["geometry"]) for f in land["features"]] + [shape(f["geometry"]).buffer(0) for f in jload(ICE)["features"]]
tree = shapely.STRtree(LP)
pts = shapely.points(ll[:, 1], ll[:, 0])
hit = tree.query(pts, predicate="intersects")
is_land = np.zeros(N, bool); is_land[hit[0]] = True
adm = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
names = [f["properties"]["NAME"] for f in adm["features"]]
conts = [f["properties"]["CONTINENT"] for f in adm["features"]]
AP = [shape(f["geometry"]) for f in adm["features"]]
at = shapely.STRtree(AP)
country = np.full(N, -1, np.int32)
h2 = at.query(pts, predicate="intersects")
country[h2[0]] = h2[1]
# land cells outside every country polygon (small coastal slivers): nearest country
miss = np.where(is_land & (country < 0))[0]
if len(miss):
    near = at.nearest(pts[miss])
    country[miss] = near
print("land cells", is_land.sum(), "land area", round(area[is_land].sum()), "km2; no country", len(miss))
# first-level divisions (Natural Earth 10m admin-1) for the survey and settlement layer: ISO 3166-2 code and country code
a1 = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")["features"]
A1P = [shape(f["geometry"]) for f in a1]
t1 = shapely.STRtree(A1P)
iso = np.full(N, "", dtype=object); a3 = np.full(N, "", dtype=object)
li = np.where(is_land)[0]
h1 = t1.query(pts[li], predicate="intersects")
for i, k in zip(li[h1[0]], h1[1]):
    iso[i] = a1[k]["properties"]["iso_3166_2"] or ""; a3[i] = a1[k]["properties"]["adm0_a3"] or ""
miss1 = li[iso[li] == ""]
if len(miss1):
    nn = t1.nearest(pts[miss1])
    for i, k in zip(miss1, nn):
        iso[i] = a1[k]["properties"]["iso_3166_2"] or ""; a3[i] = a1[k]["properties"]["adm0_a3"] or ""
print("admin-1 assigned to", int((iso != "").sum()), "land cells")
np.savez_compressed(f"{WORK}/grid.npz", cells=np.array(cells), lat=ll[:, 0], lon=ll[:, 1], area=area, land=is_land, nb=nb,
                    country=country, cnames=np.array(names), cconts=np.array(conts), iso=iso.astype(str), a3=a3.astype(str))


def lookup(lats, lons):
    out = np.empty(lats.size, np.int32)
    for k, (a, b) in enumerate(zip(lats.ravel(), lons.ravel())):
        out[k] = idx[h3.latlng_to_cell(a, b, H3_RES)]
    return out.reshape(lats.shape)


def land_mask(W, H, bounds, proj=None):
    geoms = []
    for g in LP:
        if proj is not None:
            g = shapely.transform(shapely.clip_by_rect(g, -180, -MERC_MAX, 180, MERC_MAX), proj)
        geoms.append(g)
    tr = from_bounds(*bounds, W, H)
    return features.rasterize(((g, 1) for g in geoms if not g.is_empty), out_shape=(H, W), transform=tr, all_touched=False, dtype="uint8").astype(bool)


# Web Mercator page raster
R6 = 6378137.0
ymax = R6 * np.log(np.tan(np.pi / 4 + np.radians(MERC_MAX) / 2))
xs = (np.arange(RASTER) + .5) / RASTER * 2 * ymax - ymax
lon_m = np.degrees(xs / R6)
lat_m = np.degrees(2 * np.arctan(np.exp(-xs / R6)) - np.pi / 2)          # row 0 at the top
LA, LO = np.meshgrid(lat_m, lon_m, indexing="ij")
pm = lookup(LA, LO)
merc = lambda c: np.stack([np.radians(c[:, 0]) * R6, R6 * np.log(np.tan(np.pi / 4 + np.radians(np.clip(c[:, 1], -MERC_MAX, MERC_MAX)) / 2))], 1)
lm = land_mask(RASTER, RASTER, (-ymax, -ymax, ymax, ymax), merc)
np.savez_compressed(f"{WORK}/pix_merc.npz", cell=pm, land=lm)
print("mercator raster", pm.shape, round(time.time() - t0, 1), "s")

# plate carree raster for the video and figures
H = VIDEO_W // 2
lon_p = -180 + (np.arange(VIDEO_W) + .5) * 360 / VIDEO_W
lat_p = 90 - (np.arange(H) + .5) * 180 / H
LA, LO = np.meshgrid(lat_p, lon_p, indexing="ij")
pp = lookup(LA, LO)
lp = land_mask(VIDEO_W, H, (-180, -90, 180, 90))
np.savez_compressed(f"{WORK}/pix_pc.npz", cell=pp, land=lp)
print("plate carree raster", pp.shape, round(time.time() - t0, 1), "s")
