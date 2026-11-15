"""Sondeo de estados del mapa y clic en gráficos (spike FE-05).

Requiere playwright (Python), Chrome y `npm run dev` en marcha. Imprime JSON; no hace afirmaciones por sí solo.

    python scripts/probe_states.py http://127.0.0.1:5173

Cubre: (1) error de red en un mes + botón "Reintentar"; (2) respuesta tardía de un mes anterior que NO debe
pisar al mes elegido después; (3) clic sobre un punto de cada gráfico cambia el mes (y el mapa lo sigue).
Chrome headless con WebGL por software: sirve para comprobar comportamiento, no rendimiento.
"""

import json
import sys
import time

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5199"
ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"]
CHROME = "/usr/bin/google-chrome"

states = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, headless=True, args=ARGS)
    page = b.new_context(viewport={"width": 1280, "height": 900}).new_page()
    state = lambda: page.evaluate("(() => { const f = document.querySelector('[data-testid=map-frame]'); return { status: f.dataset.status, visible: f.dataset.visibleMonth, month: document.querySelector('.timeline__month-id').textContent, alert: document.querySelector('.map-message')?.innerText || '', retry: !!document.querySelector('.map-message button') } })()")
    # 1) error de red en 2005-02 + reintento
    blocked = {'on': True}
    def handler(route):
        if blocked['on']: route.abort()
        else: route.continue_()
    page.route("**/frames/mercator/2005-02.png", handler)
    page.goto(URL, wait_until="load")
    page.wait_for_selector('[data-testid="map-frame"][data-status="ready"]', timeout=30000)
    page.get_by_role('button', name='Siguiente').click(); page.wait_for_timeout(1200)
    states['error_2005-02'] = state()
    blocked['on'] = False
    page.locator('.map-message button').click(); page.wait_for_timeout(1500)
    states['tras_reintentar'] = state()
    page.unroute("**/frames/mercator/2005-02.png")
    # 2) respuesta tardía: 2005-02 llega 1.5 s tarde, el usuario ya pasó a 2005-03
    page.goto(URL, wait_until="load")
    page.wait_for_selector('[data-testid="map-frame"][data-status="ready"]', timeout=30000)
    def slow(route):
        time.sleep(1.5); route.continue_()
    page.route("**/frames/mercator/2005-02.png", slow)
    page.get_by_role('button', name='Siguiente').click()      # pide 2005-02 (lento)
    page.wait_for_timeout(150)
    page.get_by_role('button', name='Siguiente').click()      # pasa a 2005-03 (rápido)
    page.wait_for_timeout(3500)
    states['respuesta_tardia'] = state()
    b.close()

clicks = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, headless=True, args=ARGS)
    for idx, name in ((0, 'echarts'), (1, 'recharts')):
        page = b.new_context(viewport={"width": 1280, "height": 900}).new_page()
        page.goto(URL, wait_until="load")
        page.wait_for_selector('[data-testid="map-frame"][data-status="ready"]', timeout=30000)
        month = lambda: page.evaluate("document.querySelector('.timeline__month-id')?.textContent")
        c = page.locator('.chart').nth(idx); box = c.bounding_box()
        res = {'inicio': month()}
        # mover primero (ECharts necesita hover para activar el eje), luego clic sobre 2005-02 y 2005-07
        for label, dx, dy in (('2005-02', 108, 83), ('2005-07', 290, 70)):
            page.mouse.move(box['x'] + dx, box['y'] + dy); page.wait_for_timeout(250)
            page.mouse.click(box['x'] + dx, box['y'] + dy); page.wait_for_timeout(400)
            res[f'tras_clic_{label}'] = month()
        res['map_status'] = page.evaluate("document.querySelector('[data-testid=map-frame]').dataset.status")
        clicks[name] = res
        page.context.close()
    b.close()

print(json.dumps({"estados": states, "clic_en_graficos": clicks}, indent=1, ensure_ascii=False))
