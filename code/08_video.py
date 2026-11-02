"""Videos of the Europe timeline (release/video/known-world_1920x1080.mp4 and known-world_1080x1920.mp4), from the same
model as the page: the plate carree raster coloured frame by frame, routes drawn as they happen with the leader's label,
and the two bars. Frames are piped to ffmpeg (libx264). Time runs on the page's uneven scale, 1400 BC to 1960."""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFont
from figstyle import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "video"); os.makedirs(OUT, exist_ok=True)
FPS, SECS, HOLD = 30, 72, 4
VP = "europe"
PS = pix_state(VP)
SER = series(S[VP]); SERA = {vp: series(S[vp]) for vp in VIEWPOINTS}
JV = [e for e in J if e["viewpoint"] == VP and e["mode"] != "base"]
NEWA = {}
m = S[VP]["by"] >= 0
a = np.bincount(S[VP]["by"][m], weights=AREA[m], minlength=len(S[VP]["ids"]))
for k, jid in enumerate(S[VP]["ids"]): NEWA[jid] = a[k]
MOM = [m for m in jload(f"{DATA}/site.json")["moments"] if m["v"] == VP]
fnt = lambda f, s: ImageFont.truetype(f, s)


def cent_col(y):
    return CENT[(y // 100) % 7]


def hexrgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def render_map(t, W):
    H = W // 2
    base = Image.fromarray(frame_rgb(PS, t)).resize((W, H), Image.NEAREST)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    pos = year_pos(t); labs = []
    for e in JV:
        if e["start"] > t: continue
        active = pos <= year_pos(e["end"]) + .013
        xy = journey_xy(e, t, W, H)
        if not xy: continue
        col = hexrgb(cent_col(e["start"]))
        for k in (-1, 0, 1):
            pts = [(x + k * W, y) for x, y in xy]
            if max(p[0] for p in pts) < 0 or min(p[0] for p in pts) > W: continue
            if len(pts) > 1:
                d.line(pts, fill=col + ((255,) if active else (70,)), width=max(2, W // 700) if active else 1, joint="curve")
            if active and 0 <= pts[-1][0] <= W:
                labs.append((NEWA.get(e["id"], 0), e["label"], pts[-1], col, min(1, (year_pos(e["end"]) + .013 - pos) / .006)))
    img = Image.alpha_composite(base.convert("RGBA"), ov)
    d = ImageDraw.Draw(img); f = fnt(F_MONOM, max(13, W // 95)); boxes = []
    for _, lab, (x, y), col, al in sorted(labs, key=lambda r: -r[0])[:14]:
        w = d.textlength(lab, font=f) + 12; h = f.size + 8
        bx = (x + 7, y - h / 2, x + 7 + w, y + h / 2)
        if bx[2] > W: bx = (x - 7 - w, bx[1], x - 7, bx[3])
        if any(not (bx[2] < o[0] or bx[0] > o[2] or bx[3] < o[1] or bx[1] > o[3]) for o in boxes): continue
        boxes.append(bx)
        a8 = int(255 * max(.3, al))
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
        dl.rectangle(bx, fill=(12, 12, 12, int(a8 * .8))); dl.rectangle((bx[0], bx[1], bx[0] + 3, bx[3]), fill=col + (a8,))
        dl.text((bx[0] + 8, y), lab, font=f, fill=(255, 255, 255, a8), anchor="lm"); dl.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 255, 255, a8))
        img = Image.alpha_composite(img, lay)
    return img.convert("RGB")


def year_txt(t):
    t = int(round(t))
    return (f"{-t}", "BC") if t < 0 else ((f"{max(1, t)}", "AD") if t < 1000 else (str(t), ""))


def header(d, W, x0, y0, t, big, scale):
    """Red title bar, year and the two bars."""
    d.rectangle((0, y0, W, y0 + int(74 * scale)), fill=(178, 52, 34))
    d.text((x0, y0 + int(37 * scale)), "The world as recorded for Europe", font=fnt(F_BLACK, int(38 * scale)), fill="white", anchor="lm")
    yy = y0 + int(74 * scale) + int(18 * scale)
    n, era = year_txt(t)
    fy = fnt(F_BLACK, big)
    d.text((x0, yy), n, font=fy, fill="white", anchor="lt")
    if era: d.text((x0 + d.textlength(n, font=fy) + 10, yy + big * .62), era, font=fnt(F_MONOM, int(big * .32)), fill=(216, 207, 191), anchor="lt")
    i = int(round(t)) - YEAR0
    return yy, i


def bars(d, x, y, w, t, scale):
    i = int(round(t)) - YEAR0
    fm_ = fnt(F_MONOM, int(24 * scale))
    for k, (lab, key, col) in enumerate((("Land known", "land", (236, 228, 212)), ("Earth's surface known", "surface", (79, 127, 174)))):
        yy = y + k * int(52 * scale)
        v = SER[key][i]
        d.text((x, yy), lab, font=fm_, fill=(231, 224, 210), anchor="lm")
        bx0 = x + int(330 * scale); bx1 = x + w - int(100 * scale)
        d.rectangle((bx0, yy - int(9 * scale), bx1, yy + int(9 * scale)), fill=(44, 44, 44))
        d.rectangle((bx0, yy - int(9 * scale), bx0 + (bx1 - bx0) * v, yy + int(9 * scale)), fill=col)
        d.text((x + w, yy), f"{100 * v:.0f}%" if v >= .1 else f"{100 * v:.1f}%", font=fm_, fill="white", anchor="rm")


def moment_txt(t):
    ms = [m for m in MOM if m["y"] <= t]
    return ms[-1] if ms else None


def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if d.textlength(cur + " " + w, font=font) > width and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return lines + [cur]


CREDIT = f"Dr Tristan Hotham · maps.tristanhotham.com/known-world · {R['data']['journeys']} journeys in a gazetteer compiled for this study; Natural Earth"


def frame_land(t):
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), (17, 17, 17)); d = ImageDraw.Draw(img)
    yy, _ = header(d, W, 40, 0, t, 96, 1.0)
    bars(d, 520, yy + 34, 1360, t, 1.0)
    mp = render_map(t, 1800)
    img.paste(mp.crop((0, 0, 1800, 780)), (60, 230))       # 90N to 66S: the far south is cropped
    m = moment_txt(t)
    if m:
        f = fnt(F_MONO, 22)
        d.text((60, 1030), f"{yr(m['y'])} · {m['t']}. {m['x']}"[:150], font=f, fill=(231, 224, 210), anchor="lm")
    d.text((1860, 1062), CREDIT, font=fnt(F_MONO, 15), fill=(150, 145, 135), anchor="rm")
    return img


def frame_vert(t):
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), (17, 17, 17)); d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 150), fill=(178, 52, 34))
    d.text((40, 52), "The Known World", font=fnt(F_BLACK, 64), fill="white", anchor="lm")
    d.text((40, 114), "How much of the Earth Europe had recorded", font=fnt(F_MONOM, 26), fill=(255, 235, 225), anchor="lm")
    n, era = year_txt(t); fy = fnt(F_BLACK, 150)
    d.text((40, 180), n, font=fy, fill="white", anchor="lt")
    if era: d.text((40 + d.textlength(n, font=fy) + 14, 270), era, font=fnt(F_MONOM, 48), fill=(216, 207, 191), anchor="lt")
    bars(d, 40, 400, 1000, t, 1.2)
    mp = render_map(t, 1080).crop((0, 0, 1080, 480))       # whole width, 90N to 70S
    img.paste(mp, (0, 560))
    # chart of land share, all viewpoints, growing with time
    cx0, cx1, cy0, cy1 = 90, 1030, 1180, 1560
    d.text((40, 1140), "Share of the world's land recorded", font=fnt(F_MONOM, 26), fill=(231, 224, 210), anchor="lm")
    for v in (0, 20, 40, 60):
        y = cy1 - v / 70 * (cy1 - cy0); d.line((cx0, y, cx1, y), fill=(50, 50, 50)); d.text((cx0 - 10, y), f"{v}%", font=fnt(F_MONO, 20), fill=(150, 145, 135), anchor="rm")
    p0 = year_pos(-1400)
    X = lambda y: cx0 + (year_pos(y) - p0) / (1 - p0) * (cx1 - cx0)
    for v in ("polynesia", "china", "islamic", "europe"):
        ys = list(range(-1400, int(t) + 1, 5)) + [int(t)]
        pts = [(X(y), cy1 - 100 * SERA[v]["land"][y - YEAR0] / 70 * (cy1 - cy0)) for y in ys]
        if len(pts) > 1: d.line(pts, fill=hexrgb(VPC_D[v]), width=5 if v == "europe" else 3)
    for k, v in enumerate(VIEWPOINTS):
        x = 90 + k * 245; d.rectangle((x, 1600, x + 26, 1612), fill=hexrgb(VPC_D[v])); d.text((x + 34, 1606), VP_SHORT[v], font=fnt(F_MONO, 22), fill=(231, 224, 210), anchor="lm")
    for y_ in (-1000, 1, 1000, 1500, 1800, 1960):
        d.text((X(y_), cy1 + 16), yr(y_), font=fnt(F_MONO, 18), fill=(150, 145, 135), anchor="mt")
    m = moment_txt(t)
    if m:
        f = fnt(F_MONOM, 30); d.text((40, 1680), f"{yr(m['y'])} · {m['t']}", font=f, fill="white", anchor="lm")
        for k, ln in enumerate(wrap(d, m["x"], fnt(F_MONO, 26), 1000)[:3]):
            d.text((40, 1726 + k * 36), ln, font=fnt(F_MONO, 26), fill=(231, 224, 210), anchor="lm")
    d.text((40, 1890), "Dr Tristan Hotham · maps.tristanhotham.com/known-world", font=fnt(F_MONO, 22), fill=(150, 145, 135), anchor="lm")
    return img


def make(name, fn, size):
    W, H = size
    path = f"{OUT}/known-world_{name}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "27", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
    p0 = year_pos(-1400); n = FPS * SECS
    for k in range(n + FPS * HOLD):
        t = round(pos_year(p0 + (1 - p0) * min(1, k / n)))
        t = 1 if t == 0 else t
        p.stdin.write(fn(t).tobytes())
    p.stdin.close(); p.wait()
    print(path, round(os.path.getsize(path) / 1e6, 1), "MB")
    return round(os.path.getsize(path) / 1e6, 1)


if __name__ == "__main__":
    if "test" in sys.argv:
        frame_land(1777).save(f"{WORK}/v_land.png"); frame_vert(1520).save(f"{WORK}/v_vert.png"); sys.exit()
    sizes = {"1920x1080": make("1920x1080", frame_land, (1920, 1080)), "1080x1920": make("1080x1920", frame_vert, (1080, 1920))}
    jsave(sizes, f"{OUT}/sizes.json")
    assert all(v < 25 for v in sizes.values())
