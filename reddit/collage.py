"""Reddit collage (reddit/known_world.png, 2400 px wide, light paper): Europe's known world at eight dates and the share of
land known by point of view. Numbers from data/results.json; maps from the reveal model."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.patheffects as pe
from figstyle import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "reddit", "known_world.png")
SER = {vp: series(S[vp]) for vp in VIEWPOINTS}
HALO = [pe.withStroke(linewidth=3.5, foreground=BG)]
DATES = [150, 1000, 1450, 1550, 1700, 1800, 1900, 1960]
ps = pix_state("europe")
SEA2 = np.array([58, 92, 128])          # a quieter sea than the page, so ship bands read less as ribbons
sh = R["share"]["europe"]
assert [sh[str(y)]["land"] for y in (1492, 1800, 1900)] == [20.0, 44.3, 67.3]

fig = plt.figure(figsize=(12, 17.5), facecolor=BG)
gs = fig.add_gridspec(6, 2, height_ratios=[1, 1, 1, 1, 1.45, .42], left=.04, right=.96, top=.89, bottom=.06, hspace=.32, wspace=.05)
fig.text(.04, .985, "How much of the world Europe had mapped", fontproperties=DISP, fontsize=33, color=FG, va="top")
fig.text(.04, .953, "1400 BC to 1960: land and sea within reach of recorded journeys, plus regions systematically surveyed or settled",
         fontsize=12.2, color=MUT, va="top")
fig.text(.04, .934, f"In 1492 Europe's recorded world covered {sh['1492']['land']:.0f}% of the Earth's land. By 1800, {sh['1800']['land']:.0f}%. By 1900, {sh['1900']['land']:.0f}%.",
         fontsize=13.5, color=RED, va="top")
for k, y in enumerate(DATES):
    r, c = divmod(k, 2)
    ax = fig.add_subplot(gs[r, c])
    rgb = frame_rgb(ps, y, sea=SEA2)[: int(900 * 156 / 180)]
    ax.imshow(rgb, extent=[-180, 180, -66, 90], interpolation="nearest", aspect="equal")
    ax.set_xticks([]); ax.set_yticks([]); [s_.set_visible(False) for s_ in ax.spines.values()]
    i = y - YEAR0
    ax.text(0, 1.03, yr(y), transform=ax.transAxes, fontproperties=DISP, fontsize=19, color=FG, va="bottom")
    ax.text(1, 1.03, f"land {100 * SER['europe']['land'][i]:.0f}%  ·  sea and land {100 * SER['europe']['surface'][i]:.0f}%", transform=ax.transAxes, fontsize=10.5, color=MUT, va="bottom", ha="right")
axc = fig.add_subplot(gs[4, :]); axc.set_facecolor(BG)
pb = axc.get_position(); axc.set_position([pb.x0 + .03, pb.y0, pb.width - .15, pb.height])
YRS = np.arange(YEAR0, YEAR1 + 1); XP = np.array([year_pos(y) for y in YRS])
import pickle as _pk
SJ = series(_pk.load(open(f"{WORK}/state_journeys_only.pkl", "rb"))["europe"])
axc.plot(XP, 100 * SER["polynesia"]["surface"], color=VPC_P["polynesia"], lw=2.2)
for vp in ("china", "islamic"):
    axc.plot(XP, 100 * SER[vp]["land"], color=VPC_P[vp], lw=2.2)
axc.plot(XP, 100 * SJ["land"], color=VPC_P["europe"], lw=1.8, ls=(0, (4, 3)))
axc.plot(XP, 100 * SER["europe"]["land"], color=VPC_P["europe"], lw=3)
for nm, v, col in (("Europe", 100 * SER["europe"]["land"][-1], VPC_P["europe"]), ("journeys only", 100 * SJ["land"][-1], VPC_P["europe"]), ("Islamic world", 100 * SER["islamic"]["land"][-1], VPC_P["islamic"]),
                   ("China", 100 * SER["china"]["land"][-1], VPC_P["china"]), ("Polynesia (sea)", 100 * SER["polynesia"]["surface"][-1], VPC_P["polynesia"])):
    axc.text(1.006, v, f"{nm} {v:.0f}%", color=col, fontsize=11, va="center", transform=axc.get_yaxis_transform(), path_effects=HALO)
ticks = (-1000, 1, 1000, 1400, 1500, 1600, 1700, 1800, 1900, 1960)
axc.set_xticks([year_pos(y) for y in ticks]); axc.set_xticklabels([yr(y) if y < 1000 else str(y) for y in ticks], fontsize=10)
axc.set_xlim(0, 1); axc.set_ylim(0, 85); axc.set_yticks([0, 20, 40, 60, 80]); axc.set_yticklabels(["0%", "20%", "40%", "60%", "80%"])
axc.grid(axis="y", color=RULE); [axc.spines[s_].set_visible(False) for s_ in ("top", "right")]
axc.set_title("Share of the world's land recorded, by point of view (Polynesia: sea and land)", loc="left", fontsize=12.5, color=FG, pad=10)
for y, txt, dx, dy in ((150, "Ptolemy's Geography", -10, 26), (1492, "Columbus", -6, 30), (1870, "Africa crossed, India and the West surveyed", -14, 22)):
    axc.annotate(txt, (year_pos(y), 100 * SER["europe"]["land"][y - YEAR0]), xytext=(dx, dy), textcoords="offset points", ha="right", fontsize=10, color=FG, path_effects=HALO,
                 arrowprops=dict(arrowstyle="-", color=MUT, lw=.8))
axl = fig.add_subplot(gs[5, :]); axl.axis("off")
axl.legend(handles=[Patch(color=MLAND / 255, label="Land known to Europe"), Patch(color=SEA2 / 255, label="Sea known to Europe"),
                    Patch(color=MDARK / 255, label="Not yet recorded for Europe (always known to the people living there)")] +
           [Line2D([], [], color=VPC_P[v], lw=3, label={"europe": "Europe (dashed: journeys only)", "islamic": "Islamic world (Arabic, Persian, Ottoman)", "china": "China", "polynesia": "Polynesia and Austronesia (settlement dates)"}[v]) for v in VIEWPOINTS],
           loc="upper left", ncol=2, frameon=False, fontsize=10.5)
fig.text(.04, .01, f"Data: {R['data']['journeys']} dated journey routes (a gazetteer compiled for this study from Wikipedia and published accounts); Natural Earth.\n"
         "Equal-area H3 grid; a cell lights near a route, or when its region was surveyed or settled (" f"{R['data']['surveys']} regions, dates not confirmed).\n"
         "Dr Tristan Hotham · maps.tristanhotham.com/known-world",
         fontsize=9.5, color=MUT, va="bottom")
fig.savefig(OUT, dpi=200, facecolor=BG)
plt.close(fig)
from PIL import Image
print(OUT, Image.open(OUT).size, os.path.getsize(OUT) // 1024, "KB")
