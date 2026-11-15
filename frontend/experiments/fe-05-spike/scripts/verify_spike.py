"""Verificación opcional del spike FE-05 en un Chrome real (WebGL por software).

Requiere: Python 3, `pip install playwright pillow`, Google Chrome instalado y el servidor de
desarrollo del spike corriendo (`npm run dev -- --port 5199`). Solo funciona contra `vite dev`
porque lee los contadores `window.__SPIKE__`, que existen únicamente en desarrollo.

    python scripts/verify_spike.py http://127.0.0.1:5199 ./capturas

No es parte de la app ni del CI; es una ayuda para reproducir las mediciones del documento
docs/fe-05-evaluacion-mapa-graficos.md.
"""

import io
import json
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5199"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "capturas")
OUT.mkdir(parents=True, exist_ok=True)
CHROME = "/usr/bin/google-chrome"
ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--no-sandbox"]

report: dict = {"checks": [], "console_errors": [], "external_requests": []}


def check(name: str, ok: bool, detail: object = None) -> None:
    report["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name + (f" -> {detail}" if detail is not None else ""))


def spike(page):
    return page.evaluate("window.__SPIKE__")


def wait_status(page, status: str, timeout: int = 15000) -> None:
    page.wait_for_selector(f'[data-testid="map-frame"][data-status="{status}"]', timeout=timeout)
    page.wait_for_function("window.__SPIKE_MAP__ && window.__SPIKE_MAP__.loaded()", timeout=timeout)
    page.wait_for_timeout(400)


def is_white(px) -> bool:
    return px[0] == 255 and px[1] == 255 and px[2] == 255 and px[3] == 255


def measure_ticks(page, variant: str) -> dict:
    """Mide en pantalla dónde caen las marcas de latitud -26, -30 y -34 (borde superior de la fila)."""
    box = page.locator('[data-testid="map-frame"]').bounding_box()
    shot = Image.open(io.BytesIO(page.locator('[data-testid="map-frame"]').screenshot())).convert("RGBA")
    scale = shot.size[0] / box["width"]
    projected = page.evaluate(
        """() => { const m = window.__SPIKE_MAP__;
          const p = (lon, lat) => { const r = m.project([lon, lat]); return [r.x, r.y]; };
          return { x0: p(139.0, -26)[0], x1: p(140.2, -26)[0],
                   expected: { '-26': p(139.5, -26)[1], '-30': p(139.5, -30)[1], '-34': p(139.5, -34)[1] },
                   nw: p(138, -24) }; }"""
    )
    x_mid = int(((projected["x0"] + projected["x1"]) / 2) * scale)
    out = {}
    for lat, y_expected in projected["expected"].items():
        # Primer píxel blanco puro (la marca) en una ventana vertical alrededor de lo esperado.
        top = None
        for dy in range(-int(40 * scale), int(40 * scale)):
            y = int(y_expected * scale) + dy
            if 0 <= y < shot.size[1] and is_white(shot.getpixel((x_mid, y))):
                top = y
                break
        if top is None:
            out[lat] = {"expected_px": round(y_expected, 1), "measured_px": None}
            continue
        shown_lat = page.evaluate("(y) => window.__SPIKE_MAP__.unproject([%f, y]).lat" % (x_mid / scale), top / scale)
        out[lat] = {
            "expected_px": round(y_expected, 1),
            "measured_px": round(top / scale, 1),
            "delta_px": round(top / scale - y_expected, 1),
            "latitude_shown": round(shown_lat, 3),
            "error_deg": round(shown_lat - float(lat), 3),
        }
    return out


with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME, headless=True, args=ARGS)

    # ---------- Escritorio ----------
    context = browser.new_context(viewport={"width": 1280, "height": 1000}, device_scale_factor=1)
    page = context.new_page()
    requests: list[str] = []
    page.on("request", lambda r: requests.append(r.url))
    page.on("console", lambda m: report["console_errors"].append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: report["console_errors"].append(str(e)))

    page.goto(URL, wait_until="networkidle")
    wait_status(page, "ready")
    s = spike(page)
    check("El mapa se crea una sola vez al cargar", s["mapLoads"] == 1, s)
    check("2005-01 muestra su frame", s["visibleMonth"] == "2005-01" and s["imageUpdates"] == 1)
    page.screenshot(path=str(OUT / "desktop-2005-01.png"), full_page=True)

    # Recorrer los 12 meses con "Siguiente" y comprobar el estado de cada uno.
    states = {}
    for _ in range(11):
        page.get_by_role("button", name="Siguiente").click()
        month = page.locator('[data-testid="selected-month"] .timeline__month-id').inner_text()
        has_frame = month in ("2005-02", "2005-03")
        wait_status(page, "ready" if has_frame else "missing")
        s = spike(page)
        states[month] = {"status": page.locator('[data-testid="map-frame"]').get_attribute("data-status"), "visibleMonth": s["visibleMonth"]}
        if month in ("2005-02", "2005-03", "2005-04"):
            page.locator('[data-testid="map-frame"]').screenshot(path=str(OUT / f"map-{month}.png"))
    s = spike(page)
    check("Tras recorrer 12 meses el mapa NO se reconstruyó (mapLoads sigue en 1)", s["mapLoads"] == 1, s)
    check("Solo se actualizó la imagen para los meses con frame (updateImage x3)", s["imageUpdates"] == 3, s["imageUpdates"])
    check("2005-04 (ausente a propósito) no deja ninguna capa visible", states["2005-04"]["visibleMonth"] is None and states["2005-04"]["status"] == "missing", states["2005-04"])
    check("Los meses 05..12 se declaran sin capa", all(states[m]["status"] == "missing" and states[m]["visibleMonth"] is None for m in states if m >= "2005-05"))
    report["month_states"] = states

    # Volver a 2005-03 y verificar que el mes ausente NO reutiliza otra imagen.
    page.get_by_role("button", name="Anterior").click()
    for _ in range(8):
        page.get_by_role("button", name="Anterior").click()
    wait_status(page, "ready")
    check("Al volver a 2005-03 se muestra ese mes", spike(page)["visibleMonth"] == "2005-03")

    # ---------- Georreferenciación ----------
    for variant_name, label in (("mercator", "Remuestreada a Web Mercator"), ("native", "Rejilla nativa EPSG:4326")):
        page.get_by_label(label, exact=False).check()
        page.wait_for_function("window.__SPIKE_MAP__.loaded()")
        wait_status(page, "ready")
        ticks = measure_ticks(page, variant_name)
        report[f"ticks_{variant_name}"] = ticks
        print(variant_name, json.dumps(ticks))
        page.locator('[data-testid="map-frame"]').screenshot(path=str(OUT / f"map-georef-{variant_name}.png"))
    errs_m = [abs(v["error_deg"]) for v in report["ticks_mercator"].values() if v.get("error_deg") is not None]
    errs_n = [abs(v["error_deg"]) for v in report["ticks_native"].values() if v.get("error_deg") is not None]
    check("Variante Mercator: marcas dentro de 0,1° (una celda) de su latitud real", bool(errs_m) and max(errs_m) <= 0.1, errs_m)
    check("Variante nativa estirada por bbox: error de latitud medible (>0,1°)", bool(errs_n) and max(errs_n) > 0.1, errs_n)
    page.get_by_label("Remuestreada a Web Mercator", exact=False).check()
    wait_status(page, "ready")

    # ---------- Modo contrato: sin capa y sin peticiones ----------
    before = len(requests)
    page.get_by_label("Descriptor", exact=False).first.check()
    page.wait_for_selector('[data-testid="map-frame"][data-status="missing"]')
    for _ in range(3):
        page.get_by_role("button", name="Siguiente").click()
        page.wait_for_timeout(300)
    new_requests = [u for u in requests[before:] if "/frames/" in u or "tile" in u.lower()]
    check("Modo contrato (state: unavailable): cero peticiones de imágenes o teselas", not new_requests, new_requests)
    check("Modo contrato: Reproducir deshabilitado (ningún mes tiene capa)", page.get_by_role("button", name="Reproducir").is_disabled())
    page.screenshot(path=str(OUT / "desktop-contract-unavailable.png"), full_page=True)
    page.get_by_label("Frames locales de prototipo", exact=False).check()
    wait_status(page, "ready") if False else None

    # ---------- Peticiones externas ----------
    external = sorted({u for u in requests if not u.startswith(URL) and not u.startswith("data:") and not u.startswith("blob:")})
    report["external_requests"] = external
    check("Ninguna petición a servidores externos (sin mapa base, sin claves)", not external, external)

    # ---------- Teclado y accesibilidad del mapa ----------
    focusable = page.evaluate("document.querySelector('.maplibregl-canvas').tabIndex")
    check("El canvas del mapa es alcanzable con Tab (tabindex 0)", focusable == 0, focusable)
    label = page.evaluate("document.querySelector('.maplibregl-canvas').getAttribute('aria-label')")
    check("El canvas del mapa tiene etiqueta accesible", bool(label), label)
    context.close()

    # ---------- Móvil ----------
    mobile = browser.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2, is_mobile=True, has_touch=True)
    m = mobile.new_page()
    m.goto(URL, wait_until="networkidle")
    wait_status(m, "ready")
    m.screenshot(path=str(OUT / "mobile-2005-01-top.png"))
    m.screenshot(path=str(OUT / "mobile-full.png"), full_page=True)
    overflow = m.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    check("Móvil 375px: sin desbordamiento horizontal de la página", not overflow, overflow)
    mobile.close()
    browser.close()

report["summary"] = {"passed": sum(c["ok"] for c in report["checks"]), "total": len(report["checks"])}
(OUT / "verify-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
print("console_errors:", report["console_errors"])
print(f"{report['summary']['passed']}/{report['summary']['total']} comprobaciones OK")
