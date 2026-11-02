"""House style for static figures and the video: fonts (static instances cut from the variable Fraunces in FONTS, written
to WORK), the palette, and helpers to colour the plate carree raster of the reveal model."""
import pickle
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from reveal import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
F_BLACK, F_BOLD = f"{FD}/Fraunces-Black.ttf", f"{FD}/Fraunces-Bold.ttf"
F_MONO, F_MONOM = f"{FONTS}/IBMPlexMono-Regular.ttf", f"{FONTS}/IBMPlexMono-Medium.ttf"
F_SER = f"{FONTS}/SourceSerif4-Regular.ttf"
DISP = fm.FontProperties(fname=F_BLACK); DISPB = fm.FontProperties(fname=F_BOLD)
SERP = fm.FontProperties(fname=F_SER); SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#68625A", "axes.labelcolor": "#22201C",
                     "xtick.color": "#68625A", "ytick.color": "#68625A"})
BG, FG, MUT, RULE = "#F7F2E7", "#22201C", "#68625A", "#E0D6C1"
RED = "#B23A2A"
MLAND, MSEA, MDARK = np.array([236, 228, 212]), np.array([79, 127, 174]), np.array([27, 27, 27])
VPC_P = {"europe": "#B23A2A", "islamic": "#2E8A6E", "china": "#B07A12", "polynesia": "#2F5FA7"}   # on paper
VPC_D = {"europe": "#E0533F", "islamic": "#3FB58A", "china": "#E3A72F", "polynesia": "#5C8FE0"}   # on dark
CENT = ["#ff6a52", "#ffb347", "#ffe066", "#8be08b", "#5ed0ff", "#b59bff", "#ff8fd1"]
S = pickle.load(open(f"{WORK}/state_main.pkl", "rb"))
PC = np.load(f"{WORK}/pix_pc.npz"); PCELL, PLAND = PC["cell"], PC["land"]
J = jload(f"{DATA}/expeditions.json")
JB = {e["id"]: e for e in J}


def pix_state(vp):
    s = S[vp]
    return s["first"][PCELL], s["lost"][PCELL], s["regained"][PCELL]


def frame_rgb(ps, t, land=MLAND, sea=MSEA, dark=MDARK):
    f, l, r = ps
    k = (f <= t) & ~((l <= t) & (t < r))
    out = np.empty(PCELL.shape + (3,), np.uint8); out[:] = dark
    out[k & PLAND] = land; out[k & ~PLAND] = sea
    return out


def journey_xy(e, t, W, H, lat0=90, lat1=-90):
    """Part of the route travelled by year t, as plate carree pixel coordinates (unwrapped; may leave 0..W)."""
    xs = unwrap([p[0] for p in e["waypoints"]]); pts = []
    for i, p in enumerate(e["waypoints"]):
        if p[2] > t:
            if i and e["waypoints"][i - 1][2] < p[2]:
                q = e["waypoints"][i - 1]; f = (t - q[2]) / (p[2] - q[2])
                pts.append((xs[i - 1] + f * (xs[i] - xs[i - 1]), q[1] + f * (p[1] - q[1])))
            break
        pts.append((xs[i], p[1]))
    return [((x + 180) / 360 * W, (lat0 - y) / (lat0 - lat1) * H) for x, y in pts]
