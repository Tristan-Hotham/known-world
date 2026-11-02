"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23897793, https://doi.org/10.5281/zenodo.23897793 and https://blog.tristanhotham.com/2026/10/31/known-world/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "06_build_site.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))          # shared fact checks
R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_KnownWorld"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}

# words and alt text in the blog
assert R["regions"]["hawaii"]["europe_earliest"] - R["regions"]["hawaii"]["polynesia"] > 500          # "more than five centuries"
assert 57.5 < R["sens_range"]["land_1960_min"] < 58.5 and 85 < R["sens_range"]["land_1960_max"] < 86.5      # alt text "about 58% and 86%"
assert round(R["share"]["europe"]["150"]["land"]) == 15 and round(R["share"]["europe"]["1960"]["land"]) == 80 and round(R["journeys_only"]["share"]["1960"]["land"]) == 64
assert 2.5 < R["share"]["polynesia"]["1960"]["surface"] < 3.5
assert 18 <= R["share"]["islamic"]["1960"]["land"] < 20 and 14 <= R["share"]["china"]["1960"]["land"] < 16   # "about 19%", "about 15%"

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
from PIL import Image
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, (img, Image.open(f"{REL}/blog/{img}").size)
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
S = R["share"]["europe"]
meta = {"title": "The Known World",
        "slug": "known-world",
        "excerpt": f"A dark world that lights up as travellers wrote it down. From {R['data']['journeys']} journeys: Europe's recorded world covered {S['1492']['land']:.0f}% of the land in 1492 and {S['1900']['land']:.0f}% in 1900, and much of the dark had been recorded by China, the Islamic world or Polynesian voyagers first.",
        "seo_description": f"How much of the Earth Europe, the Islamic world, China and Polynesia had recorded, 2200 BC to 1960, mapped from {R['data']['journeys']} journeys.",
        "tags": ["maps", "history", "exploration", "data visualisation", "Polynesia", "Islamic geography", "China", "cartography"],
        "header_alt": f"Title card reading 'The Known World' in black and red on pale paper, beside four strips of a black world map lit in cream and blue for 1000, 1550, 1800 and 1960. Text: Europe's recorded world in 1492, {S['1492']['land']:.0f}% of the land; 1800, {S['1800']['land']:.0f}%; 1900, {S['1900']['land']:.0f}%."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/known-world_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"known-world/{d}/{fn}")
    for fn in ("README.md", "LICENSE", "index.html"):
        z.write(os.path.join(ROOT, fn), f"known-world/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "known-world/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("\\textsuperscript{2}", "2").replace("\\textit{Geography}", "Geography").replace("``", "\"").replace("''", "\"")
assert "\\" not in ab, ab[:200]
zmeta = {"title": "The Known World: How Much of the Earth Each Tradition Had Written About, from the Bronze Age to 1960",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Sources: a gazetteer of journey routes compiled for this study, mostly from English Wikipedia (CC BY-SA 4.0) and the accounts it cites; Natural Earth (public domain); H3 (Apache 2.0).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["history of exploration", "historical geography", "travel accounts", "Polynesian voyaging", "Islamic geography", "Chinese geography", "H3", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://en.wikipedia.org/", "relation": "isDerivedFrom", "resource_type": "other"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
