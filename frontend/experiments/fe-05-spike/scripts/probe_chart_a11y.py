"""Sondeo de accesibilidad de los dos gráficos (spike FE-05). Solo inspección automática, NO reemplaza
una prueba con lector de pantalla real.

    python scripts/probe_chart_a11y.py http://127.0.0.1:5199
"""

import json
import sys

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5199"
ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"]

PROBE = """(root) => {
  const el = document.querySelectorAll('.chart')[root]
  const focusables = [...el.querySelectorAll('a[href],button,input,select,textarea,[tabindex]')]
    .filter((n) => n.tabIndex >= 0)
    .map((n) => `${n.tagName.toLowerCase()}[tabindex=${n.getAttribute('tabindex')}]${n.getAttribute('role') ? '[role=' + n.getAttribute('role') + ']' : ''}`)
  const withAria = [...el.querySelectorAll('[aria-label],[role]')].slice(0, 8).map((n) => ({
    tag: n.tagName.toLowerCase(), role: n.getAttribute('role'), label: (n.getAttribute('aria-label') || '').slice(0, 140),
  }))
  return { focusables, withAria, svg: !!el.querySelector('svg'), canvas: !!el.querySelector('canvas') }
}"""

out = {}
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True, args=ARGS)
    page = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()
    page.goto(URL, wait_until="load")
    page.wait_for_selector('[data-testid="map-frame"][data-status="ready"]', timeout=30000)
    for key, selector in (("echarts", 0), ("recharts", 1)):
        out[key] = {"dom": page.evaluate(PROBE, selector)}
    # Recorrido por teclado: ¿se puede llegar a los puntos del gráfico y leerlos sin ratón?
    for key, selector in (("echarts", 0), ("recharts", 1)):
        page.focus("body")
        page.evaluate("document.activeElement && document.activeElement.blur()")
        tabs = []
        found_inside = False
        for _ in range(60):
            page.keyboard.press("Tab")
            info = page.evaluate(
                """(idx) => { const a = document.activeElement; const inside = !!a.closest('.chart') && a.closest('.chart') === document.querySelectorAll('.chart')[idx];
                  return { inside, tag: a.tagName.toLowerCase(), role: a.getAttribute('role'), label: (a.getAttribute('aria-label')||'').slice(0,80) } }""",
                selector,
            )
            if info["inside"]:
                found_inside = True
                tabs.append(info)
                if len(tabs) >= 4:
                    break
        out[key]["tab_stops_inside_chart"] = tabs
        out[key]["reaches_chart_by_tab"] = found_inside
        if found_inside:
            before = page.evaluate("document.querySelector('.recharts-tooltip-wrapper')?.innerText || ''")
            for _ in range(3):
                page.keyboard.press("ArrowRight")
            after = page.evaluate("document.querySelector('.recharts-tooltip-wrapper')?.innerText || ''")
            out[key]["tooltip_text_after_arrows"] = after if key == "recharts" else None
            out[key]["tooltip_text_before_arrows"] = before if key == "recharts" else None
    browser.close()
print(json.dumps(out, indent=2, ensure_ascii=False))
