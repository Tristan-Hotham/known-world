"""Header card (header.png, 1200 x 630), blog figures (release/blog/b_*.png, 1800 px wide) and paper figures
(release/paper/f_*.png). Numbers from data/results.json; maps from the reveal model (figstyle.py)."""
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap, BoundaryNorm
from figstyle import *

R = jload(f"{DATA}/results.json")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
HALO = [pe.withStroke(linewidth=3, foreground=BG)]
SER = {vp: series(S[vp]) for vp in VIEWPOINTS}
EXT = [-180, 180, -90, 90]


def both(fig, name, blog=True):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        w = fig.get_size_inches()[0]
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=1800 / w, facecolor=fig.get_facecolor())
    plt.close(fig)


def mapax(ax, rgb, crop=(90, -66)):
    H = rgb.shape[0]
    r0, r1 = int((90 - crop[0]) / 180 * H), int((90 - crop[1]) / 180 * H)
    ax.imshow(rgb[r0:r1], extent=[-180, 180, crop[1], crop[0]], interpolation="nearest", aspect="equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s_ in ax.spines.values(): s_.set_visible(False)


def time_axis(ax, y0=-1400):
    ticks = [y for y in ((-2000, -1000, 1, 1000, 1400, 1500, 1600, 1700, 1800, 1900, 1960) if y0 < -1500 else (-1000, -500, 1, 500, 1000, 1400, 1500, 1600, 1700, 1800, 1900, 1960)) if y >= y0]
    ax.set_xticks([year_pos(y) for y in ticks]); ax.set_xticklabels([yr(y) if y < 1000 else str(y) for y in ticks], fontsize=8.5)
    ax.set_xlim(year_pos(y0), 1)


YRS = np.arange(YEAR0, YEAR1 + 1)
XP = np.array([year_pos(y) for y in YRS])

# ---------- small multiples: Europe at eight dates ----------
DATES = [150, 1000, 1450, 1550, 1700, 1800, 1900, 1960]
ps = pix_state("europe")
fig, axs = plt.subplots(4, 2, figsize=(12, 13.2), facecolor=BG)
for ax, y in zip(axs.ravel(), DATES):
    mapax(ax, frame_rgb(ps, y))
    i = y - YEAR0
    ax.set_title(f"{yr(y)}   land {100 * SER['europe']['land'][i]:.0f}%, surface {100 * SER['europe']['surface'][i]:.0f}%", fontsize=10.5, loc="left", color=FG)
fig.subplots_adjust(left=.02, right=.98, top=.97, bottom=.02, hspace=.18, wspace=.04)
both(fig, "maps")

# ---------- the curve ----------
import pickle as _pk
SJ = series(_pk.load(open(f"{WORK}/state_journeys_only.pkl", "rb"))["europe"])
fig, ax = plt.subplots(figsize=(12, 6), facecolor=BG); ax.set_facecolor(BG)
for vp in ("china", "islamic"):
    ax.plot(XP, 100 * SER[vp]["land"], color=VPC_P[vp], lw=2)
ax.plot(XP, 100 * SER["polynesia"]["surface"], color=VPC_P["polynesia"], lw=2)
ax.plot(XP, 100 * SJ["land"], color=VPC_P["europe"], lw=1.6, ls=(0, (4, 3)))
ax.plot(XP, 100 * SER["europe"]["land"], color=VPC_P["europe"], lw=2.8)
time_axis(ax, YEAR0); ax.set_ylim(0, 85); ax.set_ylabel("Share known (%)")
ax.grid(axis="y", color=RULE); [ax.spines[s_].set_visible(False) for s_ in ("top", "right")]
for y, txt in ((150, "Ptolemy"), (1492, "1492"), (1870, "1870s")):
    ax.annotate(txt, (year_pos(y), 100 * SER["europe"]["land"][y - YEAR0]), xytext=(-8, 14), textcoords="offset points", ha="right", fontsize=9, color=FG, path_effects=HALO,
                arrowprops=dict(arrowstyle="-", color=MUT, lw=.7))
h = [Line2D([], [], color=VPC_P["europe"], lw=2.6, label="Europe, land (journeys, surveys and settlement)"), Line2D([], [], color=VPC_P["europe"], lw=1.6, ls=(0, (4, 3)), label="Europe, land (journeys only)"),
     Line2D([], [], color=VPC_P["islamic"], lw=2, label="Islamic world, land"), Line2D([], [], color=VPC_P["china"], lw=2, label="China, land"),
     Line2D([], [], color=VPC_P["polynesia"], lw=2, label="Polynesia, sea and land")]
ax.legend(handles=h, loc="upper left", frameon=False, fontsize=9.5, ncol=1)
fig.tight_layout(); both(fig, "curve")

# ---------- four points of view in 1450 ----------
fig, axs = plt.subplots(2, 2, figsize=(12, 6.9), facecolor=BG)
for ax, vp in zip(axs.ravel(), VIEWPOINTS):
    rgb_ = frame_rgb(pix_state(vp), 1450)
    if vp == "polynesia":
        rgb_ = np.roll(rgb_, rgb_.shape[1] // 2, axis=1)      # centred on the 180 degree meridian
    mapax(ax, rgb_)
    ax.set_title(f"{VP_SHORT[vp]} in 1450{' (Pacific-centred)' if vp == 'polynesia' else ''}: land {100 * SER[vp]['land'][1450 - YEAR0]:.1f}%, surface {100 * SER[vp]['surface'][1450 - YEAR0]:.1f}%", fontsize=10.5, loc="left", color=VPC_P[vp])
fig.subplots_adjust(left=.02, right=.98, top=.95, bottom=.02, hspace=.16, wspace=.04)
both(fig, "viewpoints")

# ---------- known elsewhere before Europe ----------
fe = S["europe"]["first"]
rgb = np.zeros(PCELL.shape + (3,), np.uint8); rgb[:] = (232, 225, 210); rgb[~PLAND] = (247, 242, 231)
for vp in ("polynesia", "china", "islamic"):
    f = S[vp]["first"]
    ahead = ((f < NEVER) & (f < fe))[PCELL]
    c = np.array([int(VPC_P[vp][k:k + 2], 16) for k in (1, 3, 5)])
    rgb[ahead & PLAND] = c; rgb[ahead & ~PLAND] = (c * .45 + np.array([247, 242, 231]) * .55).astype(np.uint8)
fig, ax = plt.subplots(figsize=(12, 5.6), facecolor=BG)
mapax(ax, rgb)
B = R["before_europe"]
ax.legend(handles=[Patch(color=VPC_P[v], label=f"{VP_SHORT[v]}: {B[v]['km2'] / 1e6:.1f} million km2 first, a median {B[v]['median_lead_years']} years ahead") for v in ("islamic", "china", "polynesia")],
          loc="lower left", frameon=True, facecolor=BG, edgecolor=RULE, fontsize=9)
fig.tight_layout(); both(fig, "before")

# ---------- when each place was first lit for Europe ----------
EDGES = [-1400, 1, 1000, 1492, 1600, 1700, 1800, 1850, 1900, 1961]
LABS = ["before AD 1", "1 to 999", "1000 to 1491", "1492 to 1599", "1600s", "1700s", "1800 to 1849", "1850 to 1899", "1900 to 1960"]
CM = ["#3B1F5C", "#5B2A86", "#7B3F9E", "#B5446E", "#D8624A", "#E98D3A", "#F2B544", "#F6D86B", "#FBF1A9"]
f0 = S["europe"]["first"][PCELL]
cls = np.digitize(f0, EDGES) - 1
rgb = np.zeros(PCELL.shape + (3,), np.uint8); rgb[:] = (40, 40, 40); rgb[~PLAND] = (247, 242, 231)
for k, c in enumerate(CM):
    m = (cls == k) & (f0 < NEVER)
    cc = np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)])
    rgb[m & PLAND] = cc; rgb[m & ~PLAND] = (cc * .18 + np.array([247, 242, 231]) * .82).astype(np.uint8)
fig, ax = plt.subplots(figsize=(12, 6.2), facecolor=BG)
mapax(ax, rgb)
ax.legend(handles=[Patch(color=c, label=l) for c, l in zip(CM, LABS)] + [Patch(color="#282828", label="land not lit by 1960")], loc="lower left", ncol=5, frameon=True, facecolor=BG, edgecolor=RULE, fontsize=8.5,
          title="First recorded for Europe (land strong, sea pale)", title_fontsize=9)
fig.tight_layout(); both(fig, "when")

# ---------- biggest journeys ----------
rows = R["biggest"]["all"][:10][::-1]
fig, ax = plt.subplots(figsize=(12, 5.6), facecolor=BG); ax.set_facecolor(BG)
y = np.arange(len(rows))
ax.barh(y, [r["new_km2"] / 1e6 for r in rows], color="#4f7fae", label="sea")
ax.barh(y, [r["new_land_km2"] / 1e6 for r in rows], color="#C9B98F", label="land")
ax.set_yticks(y); ax.set_yticklabels([f"{r['leader'][:40]} ({yr(r['start'])})" for r in rows], fontsize=9.5)
ax.set_xlabel("New area first lit for Europe (million km2)"); ax.legend(frameon=False, loc="lower right")
[ax.spines[s_].set_visible(False) for s_ in ("top", "right")]; ax.grid(axis="x", color=RULE)
fig.tight_layout(); both(fig, "journeys")

# ---------- sensitivity ----------
import pickle
NAMES = {"main": "Main run (with surveys)", "journeys_only": "Journeys only", "radius_half": "Radii halved", "radius_1p5": "Radii x 1.5", "no_fill": "No pocket fill", "fill_25": "Fill up to 25 cells",
         "fill_400": "Fill up to 400 cells", "confirmed_only": "Confirmed entries only", "no_base": "No starting worlds"}
COLS = {"main": FG, "journeys_only": "#9C4A1A", "radius_half": "#2F5FA7", "radius_1p5": "#7EA7E8", "no_fill": "#B07A12", "fill_25": "#E0A11B", "fill_400": "#8E2A2A", "confirmed_only": "#2E8A6E", "no_base": "#B23A2A"}
fig, ax = plt.subplots(figsize=(12, 5.6), facecolor=BG); ax.set_facecolor(BG)
for r in NAMES:
    SS = S if r == "main" else pickle.load(open(f"{WORK}/state_{r}.pkl", "rb"))
    ax.plot(XP, 100 * series(SS["europe"])["land"], color=COLS[r], lw=2.6 if r == "main" else 1.4, ls="-" if r in ("main", "journeys_only", "confirmed_only", "no_base") else (0, (4, 2)), label=NAMES[r])
time_axis(ax, -1400); ax.set_ylim(0, 90); ax.set_ylabel("Europe: share of land known (%)"); ax.grid(axis="y", color=RULE)
[ax.spines[s_].set_visible(False) for s_ in ("top", "right")]; ax.legend(frameon=False, fontsize=9, ncol=2, loc="upper left")
fig.tight_layout(); both(fig, "sensitivity")

# ---------- routes by source status (paper) ----------
STC = {"years_confirmed": "#2E8A6E", "read_by_compiler": "#2F5FA7", "years_not_confirmed": "#E0A11B", "unsourced": "#B23A2A"}
STN = {"years_confirmed": "years confirmed in cited article", "read_by_compiler": "taken from cited pages", "years_not_confirmed": "years not confirmed", "unsourced": "source not confirmed"}
fig, ax = plt.subplots(figsize=(12, 6.2), facecolor=BG)
rgb = np.zeros(PCELL.shape + (3,), np.uint8); rgb[:] = (232, 225, 210); rgb[~PLAND] = (247, 242, 231)
mapax(ax, rgb, crop=(90, -90))
for st_ in ("read_by_compiler", "years_confirmed", "years_not_confirmed", "unsourced"):
    for e in J:
        if e["source_status"] != st_ or e["mode"] == "survey": continue
        xs = np.array(unwrap([p[0] for p in e["waypoints"]])); ys = np.array([p[1] for p in e["waypoints"]])
        for k in (-360, 0, 360):
            if e["mode"] == "base": ax.scatter(xs + k, ys, s=1.5, color=STC[st_], lw=0)
            else: ax.plot(xs + k, ys, color=STC[st_], lw=.6 if st_ in ("read_by_compiler", "years_confirmed") else 1.1, alpha=.85)
ax.set_xlim(-180, 180); ax.set_ylim(-90, 90)
ax.legend(handles=[Line2D([], [], color=STC[k], lw=2, label=f"{STN[k]} ({R['data']['by_status'][k]})") for k in STC], loc="lower left", frameon=True, facecolor=BG, edgecolor=RULE, fontsize=9)
fig.tight_layout(); both(fig, "status", blog=False)

# ---------- header card ----------
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 630
card = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(card)
f = lambda p, s: ImageFont.truetype(p, s)
d.text((48, 50), "DATA STUDY · HISTORY", font=f(F_MONOM, 18), fill=RED)
d.text((48, 82), "The Known", font=f(F_BLACK, 84), fill=FG); d.text((48, 168), "World", font=f(F_BLACK, 84), fill=RED)
s = R["share"]["europe"]
lines_ = [f"How much of the Earth each tradition", "had recorded, 2200 BC to 1960.", "",
          f"Europe's recorded world in 1492: {s['1492']['land']:.0f}% of the land.", f"By 1800: {s['1800']['land']:.0f}%. By 1900: {s['1900']['land']:.0f}%."]
for k, ln in enumerate(lines_):
    d.text((48, 290 + k * 34), ln, font=f(F_MONO, 21), fill=FG)
d.text((48, 576), "Dr Tristan Hotham · maps.tristanhotham.com/known-world", font=f(F_MONO, 16), fill=MUT)
for k, y in enumerate((1000, 1550, 1800, 1960)):
    m = Image.fromarray(frame_rgb(ps, y)[0:780]).resize((520, 225), Image.LANCZOS)
    x0, y0 = 650, 22 + k * 151
    card.paste(m.crop((0, 0, 520, 140)), (x0, y0))
    d.rectangle((x0, y0, x0 + 70, y0 + 26), fill=(178, 52, 34)); d.text((x0 + 35, y0 + 13), yr(y), font=f(F_MONOM, 15), fill="white", anchor="mm")
card.save(os.path.join(ROOT, "header.png"))
print("figures done", sorted(os.listdir(BL)))
