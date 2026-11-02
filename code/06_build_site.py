"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json, which is embedded; the map data (data/site.json, rasters, borders) is fetched by the page.
Facts stated in words are checked here. 10.5281/zenodo.23897793, https://doi.org/10.5281/zenodo.23897793 and https://blog.tristanhotham.com/2026/10/31/known-world/ stay as placeholders for the publisher."""
import json
from common import *

R = jload(f"{DATA}/results.json")
KEEP = {"DOI", "BLOG_URL", "DOI_URL"}

# facts stated in words (page, blog, paper, collage)
S, M = R["share"], R["milestones"]
assert S["europe"]["1400"]["land"] < 20 and S["europe"]["150"]["land"] - S["europe"]["1"]["land"] > 5      # Ptolemy the first big step
assert S["europe"]["1400"]["land"] - S["europe"]["150"]["land"] < 5                                          # "very little" for a millennium
assert M["surface"]["50"] < M["land"]["50"]                                                                    # the sea first
assert max(R["century_gain"], key=R["century_gain"].get) == "1800"                                             # 19th century adds most
assert R["fastest"]["land_decade_after_1400"] == 1870
assert R["overtake"]["islamic"]["land"] is None and R["overtake"]["china"]["land"] < 0                          # never behind the Islamic world
assert R["overtake"]["polynesia"]["land"] <= R["overtake"]["china"]["land"]                                    # leads all three from then
assert R["sensitivity"]["confirmed_only"]["overtake_islamic"] > 1400
assert [c["country"] for c in R["before_europe"]["china"]["top_countries"][:3]] == ["China", "Russia", "Mongolia"]
assert R["regions"]["japan"]["china_earliest"] < 300 and R["regions"]["japan"]["europe_earliest"] == 1549
assert R["biggest"]["all"][0]["id"].startswith("cook") and R["biggest"]["all"][1]["id"].startswith("magellan")
assert "Messerschmidt" in R["biggest"]["land"][2]["leader"]
assert [c["country"] for c in R["last_lit"]["after_1900_top"][:4]] == ["Canada", "Antarctica", "Brazil", "United States of America"]
least = {c["country"] for c in R["last_lit"]["least_known_1960"]}
assert {"Cameroon", "Mauritania", "Central African Rep.", "Indonesia", "Greenland"} <= least
assert R["last_lit"]["by_half"][1]["country"] == "Canada"                                                      # "its north mapped from the air"
assert R["milestones"]["land"]["75"] is not None and R["journeys_only"]["milestones"]["land"]["50"] > R["milestones"]["land"]["50"]
assert R["sensitivity"]["journeys_only"]["land"]["1960"] == R["journeys_only"]["share"]["1960"]["land"]
assert all(v["land"]["1960"] > v["land"]["1800"] > v["land"]["1492"] for v in R["sensitivity"].values())     # shape survives
assert 2.5e5 < R["grid"]["fill_km2"] < 2.8e5                                                                   # "roughly the size of the UK"
assert R["share"]["polynesia"]["1400"]["surface"] > 5 * R["share"]["polynesia"]["1400"]["land"]


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{(?!DOI\}\}|BLOG_URL\}\}|DOI_URL\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    left = set(re.findall(r"\{\{([^}]*)\}\}", html))
    assert left <= KEEP, left
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
