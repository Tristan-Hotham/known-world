// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server PORT; set PORT). Leaflet comes from a local npm
// copy (LEAFLET_DIST) because the CDN is not reachable from the build container; tiles are blocked here.
const { chromium } = require("playwright");
const fs = require("fs");
const LD = process.env.LEAFLET_DIST;
(async () => {
  fs.mkdirSync("qa", { recursive: true });
  const b = await chromium.launch();
  const errs = [];
  for (const [nm, vw, vh] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic|jsdelivr/, r => r.abort());
    await p.route(/leaflet\.min\.js/, r => r.fulfill({ path: LD + "/leaflet.js", contentType: "application/javascript" }));
    await p.route(/leaflet\.min\.css/, r => r.fulfill({ path: LD + "/leaflet.css", contentType: "text/css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to load resource/i.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + process.env.PORT + "/index.html", { waitUntil: "load" });
    await p.waitForTimeout(3500);
    const jpg = f => `qa/${nm}_${f}.jpg`;
    await p.screenshot({ path: jpg("top"), type: "jpeg", quality: 70 });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(700); await p.locator(sel).screenshot({ path: jpg(f), type: "jpeg", quality: 72 }); };
    await shot("#stage", "map1400");
    const t0 = Date.now();
    for (const v of [0, 150, 300, 450, 600, 750, 900, 1000]) { await p.locator("#slider").fill(String(v)); }
    console.log(nm, "slider sweep ms", Date.now() - t0);
    await p.locator("#slider").fill("1000"); await p.waitForTimeout(500); await shot("#stage", "map1960");
    await p.locator("#momRow .cbtn", { hasText: "Columbus" }).click(); await p.waitForTimeout(800); await shot("#stage", "map1492");
    await p.locator("#map").click({ position: { x: Math.round(vw * .55), y: 160 } }); await p.waitForTimeout(1500); await shot("#side", "side");
    await p.locator("#stage").screenshot({ path: jpg("popup"), type: "jpeg", quality: 72 });
    for (const v of ["polynesia", "china", "islamic", "all"]) { await p.locator(`#vpRow .cbtn[data-v="${v}"]`).click(); await p.waitForTimeout(2000); await p.locator("#slider").fill("700"); await p.waitForTimeout(400); await shot("#stage", "vp_" + v); }
    await p.locator(`#vpRow .cbtn[data-v="europe"]`).click(); await p.waitForTimeout(1500);
    await p.fill("#q", "Timbuktu"); await p.waitForTimeout(300); await p.keyboard.press("Enter"); await p.waitForTimeout(2000); await shot("#stage", "search"); await shot("#side", "search_side");
    await p.locator(".lyrBtn").click(); await p.waitForTimeout(200);
    for (const k of ["coast", "borders", "names"]) await p.locator(`input[data-l="${k}"]`).check();
    await p.waitForTimeout(1500); await shot("#stage", "layers");
    await p.locator(".lyrBtn").click();
    for (const c of ["#curve", "#beforeChart", "#bigTable", "#sensTable"]) await shot(c, c.slice(1));
    await p.locator("#bigTable tr[data-j]").first().click(); await p.waitForTimeout(2000); await shot("#stage", "journey");
    await p.locator("#play").click(); await p.waitForTimeout(2500); await p.locator("#play").click(); await shot("#stage", "played");
    if (nm === "phone") {
      await p.click("#theme"); await p.waitForTimeout(800); await shot("#curve", "dark_curve");
      await p.locator("#stage .mfs-btn").click(); await p.waitForTimeout(1500); await p.screenshot({ path: jpg("fullscreen"), type: "jpeg", quality: 70 });
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
