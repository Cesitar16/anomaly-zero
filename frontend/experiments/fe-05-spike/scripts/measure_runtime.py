"""Medición opcional de tiempos y memoria al cambiar de mes (spike FE-05).

Requiere: playwright, Google Chrome y `npm run dev -- --port 5199` en marcha.
    python scripts/measure_runtime.py http://127.0.0.1:5199

AVISO: Chrome headless con WebGL por software (SwiftShader) y sin GPU. Los milisegundos NO son los de un
dispositivo real; sirven para comparar entre sí y detectar crecimientos de memoria, no como umbral de rendimiento.
"""

import json
import statistics
import sys
import time

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5199"
CHROME = "/usr/bin/google-chrome"
ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--no-sandbox", "--js-flags=--expose-gc", "--enable-precise-memory-info"]


def heap(page) -> float:
    page.evaluate("window.gc && window.gc()")
    return page.evaluate("performance.memory.usedJSHeapSize") / 1024 / 1024


def switch_to(page, month: str) -> float:
    """Mueve el slider al mes pedido y devuelve ms hasta que el mapa muestra ese mes (o declara ausencia)."""
    index = int(month[-2:]) - 1
    start = time.perf_counter()
    page.evaluate(
        """(index) => { const el = document.querySelector('.timeline__slider');
          const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
          set.call(el, String(index)); el.dispatchEvent(new Event('input', { bubbles: true })); }""",
        index,
    )
    page.wait_for_function(
        "(m) => { const f = document.querySelector('[data-testid=map-frame]'); return f.dataset.status !== 'loading' && document.querySelector('.timeline__month-id').textContent === m }",
        arg=month,
    )
    page.wait_for_function("window.__SPIKE_MAP__.loaded()")
    return (time.perf_counter() - start) * 1000


result: dict = {}
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME, headless=True, args=ARGS)
    for label, throttle in (("escritorio (sin limitar CPU)", 1), ("móvil simulado (CPU x4 más lenta)", 4)):
        ctx = browser.new_context(viewport={"width": 1280 if throttle == 1 else 390, "height": 900 if throttle == 1 else 844})
        page = ctx.new_page()
        cdp = ctx.new_cdp_session(page)
        t0 = time.perf_counter()
        page.goto(URL, wait_until="load")
        page.wait_for_selector('[data-testid="map-frame"][data-status="ready"]', timeout=30000)
        first_ready = (time.perf_counter() - t0) * 1000
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": throttle})
        page.wait_for_timeout(500)
        before = heap(page)
        times = []
        cycle = ["2005-02", "2005-03", "2005-01"]
        for i in range(60):  # 60 cambios de frame (20 vueltas por los 3 frames)
            times.append(switch_to(page, cycle[i % 3]))
        after = heap(page)
        # 12 meses completos, incluidos los ausentes, 5 vueltas.
        before12 = heap(page)
        t12 = []
        for _ in range(5):
            for m in range(1, 13):
                t12.append(switch_to(page, f"2005-{m:02d}"))
        after12 = heap(page)
        counters = page.evaluate("window.__SPIKE__")
        result[label] = {
            "primer_frame_visible_ms": round(first_ready),
            "cambio_frame_mediana_ms": round(statistics.median(times)),
            "cambio_frame_p95_ms": round(sorted(times)[int(len(times) * 0.95) - 1]),
            "heap_antes_MB": round(before, 1),
            "heap_despues_60_cambios_MB": round(after, 1),
            "heap_antes_12meses_MB": round(before12, 1),
            "heap_despues_60_cambios_de_12_meses_MB": round(after12, 1),
            "mapLoads": counters["mapLoads"],
            "imageUpdates": counters["imageUpdates"],
        }
        ctx.close()
    browser.close()
print(json.dumps(result, indent=2, ensure_ascii=False))
