"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/Hotham_KnownWorld.pdf and .tex (figures f_*.png beside them). The DOI stays a 10.5281/zenodo.23897793 placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_KnownWorld"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
cg = R["century_gain"]
top = sorted(cg, key=lambda k: -cg[k])[:3]
assert top == ["1800", "1900", "1700"], top
assert all(r["new_land_km2"] > 1e6 for r in R["biggest"]["land"][:3])
assert R["before_europe"]["islamic"]["top_countries"][0]["country"] == "Brazil"
assert R["before_europe"]["polynesia"]["pct_of_own"] == 100.0
assert R["fastest"]["land_decade"] == 140 and R["sensitivity"]["no_base"]["fastest_decade"] == 1870
assert [c["country"] for c in R["last_lit"]["least_known_1960"][:2]] == ["Cameroon", "Mauritania"] and R["last_lit"]["least_known_1960"][4]["country"] == "Indonesia" and R["last_lit"]["least_known_1960"][5]["country"].startswith("Central African")
assert R["last_lit"]["by_half"][1]["country"] == "Canada"


def tfmt(v, f):
    if v is None: return "not reached"
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "yr": return yr(v)
    if f == "mkm": return f"{float(v) / 1e6:.1f}"
    return tex(str(v))


D = R["data"]
TD = ("\\begin{table}[tbp]\\centering\\small\\caption{The gazetteer: journeys by point of view and mode, and by source status.}\\label{tab:data}"
      "\\begin{tabular}{lrrrrrrr}\\toprule Point of view & Journeys & Sea & Land & River & Sledge & Air & Base\\\\\\midrule\n")
J = [e for e in jload(f"{DATA}/expeditions.json") if e["layer"] == "journey"]
from collections import Counter
for vp in VIEWPOINTS:
    c = Counter(e["mode"] for e in J if e["viewpoint"] == vp)
    TD += f"{VP_SHORT[vp]} & {sum(c.values())} & " + " & ".join(str(c.get(m, 0)) for m in ("sea", "land", "river", "sledge", "air", "base")) + "\\\\\n"
TD += "\\midrule\\multicolumn{8}{p{14cm}}{Source status: " + "; ".join(f"{k.replace('_', ' ')} {D['by_status'][k]} ({D['status_pct'][k]:.1f}\\%)" for k in STATUS) + "}\\\\\n"
TD += f"\\multicolumn{{8}}{{p{{14cm}}}}{{Survey and settlement layer (Europe): {D['surveys']} regions, {D['survey_first']} to {D['survey_last']}, all with years not confirmed.}}\\\\\n"
TD += "\\bottomrule\\end{tabular}\\end{table}"
rows = sorted({r["id"]: r for r in R["biggest"]["all"] + R["biggest"]["land"]}.values(), key=lambda r: -r["new_km2"])
TB = ("\\begin{table}[tbp]\\centering\\small\\caption{Journeys that first lit the largest areas for Europe (million km\\textsuperscript{2}), the ten largest overall and the ten largest on land.}\\label{tab:big}"
      "\\begin{tabular}{lrrr}\\toprule Journey & Years & New area & of it land\\\\\\midrule\n" +
      "".join(f"{tex(r['leader'][:55])} & {yr(r['start'])}{'' if r['end'] == r['start'] else ' to ' + yr(r['end'])} & {r['new_km2'] / 1e6:.1f} & {r['new_land_km2'] / 1e6:.2f}\\\\\n" for r in rows) +
      "\\bottomrule\\end{tabular}\\end{table}")
B = R["before_europe"]
TBE = ("\\begin{table}[tbp]\\centering\\small\\caption{Area lit for another tradition before Europe (million km\\textsuperscript{2}), median lead in years, and the countries with most such land.}\\label{tab:before}"
       "\\begin{tabular}{lrrrrp{6cm}}\\toprule Tradition & Total & Land & Sea & Lead & Countries (land, thousand km\\textsuperscript{2})\\\\\\midrule\n" +
       "".join(f"{VP_SHORT[v]} & {B[v]['km2'] / 1e6:.1f} & {B[v]['land_km2'] / 1e6:.1f} & {B[v]['sea_km2'] / 1e6:.1f} & {B[v]['median_lead_years']} & " +
               ", ".join(f"{tex(c['country'])} {c['km2'] // 1000:,}" for c in B[v]["top_countries"][:4]) + "\\\\\n" for v in ("islamic", "china", "polynesia")) +
       "\\bottomrule\\end{tabular}\\end{table}")
N = {"main": "Main run (with surveys)", "journeys_only": "Journeys only", "radius_half": "Distances halved", "radius_1p5": "Distances x 1.5", "no_fill": "No pocket fill", "fill_25": "Fill up to 25 cells",
     "fill_400": "Fill up to 400 cells", "confirmed_only": "Confirmed entries only", "no_base": "No starting worlds"}
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Sensitivity: Europe's share of the land known (\\%) by year, the years a quarter and half of the land were lit, and the year Europe overtook China and the Islamic world on land (none: never behind).}\\label{tab:sens}"
      "\\begin{tabular}{lrrrrrrrrr}\\toprule Variant & 150 & 1492 & 1800 & 1900 & 1960 & 25\\% & 50\\% & China & Islamic\\\\\\midrule\n" +
      "".join(f"{N[k]} & {v['land']['150']:.1f} & {v['land']['1492']:.1f} & {v['land']['1800']:.1f} & {v['land']['1900']:.1f} & {v['land']['1960']:.1f} & {tfmt(v['milestones']['25'], 'raw')} & {tfmt(v['milestones']['50'], 'raw')} & {yr(v['overtake_china']) if v['overtake_china'] is not None else 'none'} & {yr(v['overtake_islamic']) if v['overtake_islamic'] is not None else 'none'}\\\\\n" for k, v in R["sensitivity"].items()) +
      "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_|DOI_LINK)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("DATA", TD), ("BIG", TB), ("BEFORE", TBE), ("SENS", TS)):
    t = t.replace("{{TABLE_%s}}" % k, v)
t = t.replace("{{DOI_LINK}}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
