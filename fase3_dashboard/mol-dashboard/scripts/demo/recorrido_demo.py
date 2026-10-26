"""DEMO-MIERCOLES Fase 4: recorrido real con sesión, screenshot por paso y errores de consola.

Uso (requiere playwright + chromium):
  python3 recorrido_demo.py https://mol-nextjs.vercel.app /ruta/para/screenshots
Pasos: 1 login VIP, 2 VIP dashboard + brecha, 3 políticas (Ocupaciones/Comparar),
4 M2 de DEMO-001 + top 10 de los 5 DEMO sin avisos vacíos, 5 Futuro DEMO-001,
6 texto libre albañil, 7 login OE. Escribe fase4.json en la carpeta de screenshots.
"""
import json
import re
import sys
import time
from playwright.sync_api import sync_playwright

BASE = sys.argv[1]
SHOTS = sys.argv[2] if len(sys.argv) > 2 else '.'
resultados = []


def paso(n, nombre, ok, shot, detalle, errores):
    resultados.append({'paso': n, 'nombre': nombre, 'ok': bool(ok) and not errores, 'screenshot': shot,
                       'detalle': detalle, 'errores_consola': errores})
    print(f"[{n}] {'OK ' if ok and not errores else 'FALLA'} {nombre} | {detalle} | errores: {errores[:3]}", flush=True)


def nuevo_contexto(b, email, pw):
    ctx = b.new_context(viewport={'width': 1366, 'height': 900})
    page = ctx.new_page()
    errs = []
    page.on('console', lambda m: errs.append(f"{page.url.replace(BASE, '')} :: {m.text[:120]}") if m.type == 'error' else None)
    page.on('pageerror', lambda e: errs.append(f"{page.url.replace(BASE, '')} :: pageerror {str(e)[:120]}"))
    page.goto(f'{BASE}/login', wait_until='networkidle')
    page.fill('#email', email); page.fill('#password', pw); page.click('button[type=submit]')
    page.wait_for_url(lambda u: '/login' not in u, timeout=30000)
    page.wait_for_load_state('networkidle')
    return ctx, page, errs


def tomar(errs):
    out = list(errs); errs.clear(); return out


with sync_playwright() as p:
    b = p.chromium.launch()

    # ===== VIP =====
    ctx, page, errs = nuevo_contexto(b, 'inversor.test@mol.demo', 'VipMOL2026!')
    shot = f'{SHOTS}/f4_1_vip.png'; page.screenshot(path=shot, full_page=True)
    paso(1, 'Login VIP → /vip', page.url.rstrip('/').endswith('/vip'), shot, page.url.replace(BASE, ''), tomar(errs))

    page.goto(f'{BASE}/vip/dashboard', wait_until='networkidle'); page.wait_for_timeout(6000)
    texto = page.inner_text('body')
    datos_hasta = 'Datos hasta el' in texto
    sin_cargar = len(re.findall(r'Cargando|Loading', texto))
    shot = f'{SHOTS}/f4_2_vip_dashboard.png'; page.screenshot(path=shot, full_page=True)
    page.goto(f'{BASE}/vip/laboratorio/brecha-formacion', wait_until='networkidle'); page.wait_for_timeout(3000)
    tb = page.inner_text('body')
    shot2 = f'{SHOTS}/f4_2b_vip_brecha.png'; page.screenshot(path=shot2, full_page=True)
    brecha_ok = ('13.976' in tb or '13976' in tb) and '77' in tb
    paso(2, '/vip/dashboard KPIs + brecha recalculada', datos_hasta and brecha_ok, f'{shot} + {shot2}',
         f"'Datos hasta el': {datos_hasta}, textos 'Cargando' tras 6 s: {sin_cargar}, brecha 13.976/77%: {brecha_ok}", tomar(errs))

    _t0 = time.time()
    page.goto(f'{BASE}/vip/politicas', wait_until='networkidle')
    page.get_by_role('button', name='Análisis de competencias').click()
    try:
        page.get_by_text('Buscar o navegar entre').wait_for(timeout=120000)
    except Exception:
        page.screenshot(path=f'{SHOTS}/f4_3_debug.png', full_page=True); raise
    carga_politicas = round(time.time() - _t0, 1)
    page.get_by_text('Buscar o navegar entre').click()
    page.get_by_placeholder('Buscar entre 3.045 ocupaciones...').fill('soldador')
    page.get_by_role('button', name=re.compile(r'^Soldador\/soldadora')).first.click()
    page.wait_for_timeout(8000)
    t3 = page.inner_text('body')
    cursos_ocup = bool(re.search(r'[Cc]urso', t3))
    shot = f'{SHOTS}/f4_3a_politicas_ocupaciones.png'; page.screenshot(path=shot, full_page=True)
    page.get_by_role('button', name='Comparar').click()
    selectores = page.get_by_text('Seleccionar ocupacion...')
    selectores.first.click(); page.get_by_placeholder('Buscar ocupacion...').fill('soldador/sold')
    page.locator('div.cursor-pointer', has_text=re.compile(r'^Soldador\/soldadora')).first.click()
    page.get_by_text('Seleccionar ocupacion...').first.click(); page.get_by_placeholder('Buscar ocupacion...').fill('calderer')
    page.locator('div.cursor-pointer', has_text=re.compile(r'^Calderero\/calderera')).first.click()
    page.wait_for_timeout(8000)
    t3b = page.inner_text('body')
    cursos_gap = bool(re.search(r'[Cc]urso', t3b))
    shot2 = f'{SHOTS}/f4_3b_politicas_comparar.png'; page.screenshot(path=shot2, full_page=True)
    paso(3, '/vip/politicas Ocupaciones (cursos) + Comparar (cursos del gap)', cursos_ocup and cursos_gap, f'{shot} + {shot2}',
         f'carga de la página: {carga_politicas} s, cursos en Ocupaciones: {cursos_ocup}, cursos en Comparar: {cursos_gap}', tomar(errs))
    ctx.close()

    # ===== OE =====
    ctx, page, errs = nuevo_contexto(b, 'oe.test@mol.demo', 'OeMOL2026!')
    shot7 = f'{SHOTS}/f4_7_oe_login.png'; page.screenshot(path=shot7, full_page=True)
    url7 = page.url.replace(BASE, '')
    errs7 = tomar(errs)

    perfiles = page.request.get(f'{BASE}/api/perfiles?limit=100').json()
    demos = {p['personas']['dni']: p['id'] for p in perfiles if (p.get('personas') or {}).get('dni', '').startswith('DEMO-')}

    page.goto(f'{BASE}/oficina-empleo/perfiles', wait_until='networkidle')
    page.get_by_role('link', name='Demo Soldador').first.click()
    page.wait_for_load_state('networkidle')
    page.get_by_role('link', name=re.compile('Oportunidades')).first.click()
    page.wait_for_url(re.compile('perfiles/matching'), timeout=30000)
    page.get_by_text('soldador/soldadora', exact=True).first.wait_for(timeout=40000)
    page.locator('button:has-text("soldador/soldadora")').first.click()
    page.get_by_text('Últimos avisos publicados').first.wait_for(timeout=30000)
    exp = page.inner_text('body')
    badges = sorted(set(re.findall(r'\b(Activa|Sin confirmar|Cerrada)\b', exp)))
    antig = bool(re.search(r'Publicado hace', exp))
    shot = f'{SHOTS}/f4_4a_m2_expandida.png'; page.screenshot(path=shot, full_page=True)
    page.get_by_role('button', name=re.compile(r'Ver (el aviso|los \d+ avisos)')).first.click()
    page.get_by_role('heading', name='Últimos avisos publicados').wait_for(timeout=30000)
    page.wait_for_timeout(2500)
    modal = page.inner_text('body')
    modal_ok = bool(re.search(r'\d+ ofertas? · \d+ activas?', modal))
    shot2 = f'{SHOTS}/f4_4b_modal_avisos.png'; page.screenshot(path=shot2)
    page.keyboard.press('Escape')

    # Ninguna de las 10 primeras ocupaciones de cada perfil DEMO con el bloque de avisos vacío
    vacios, revisadas = [], 0
    for dni, pid in sorted(demos.items()):
        page.goto(f'{BASE}/oficina-empleo/perfiles/matching?perfil_id={pid}', wait_until='networkidle')
        page.get_by_text(re.compile(r'ocupaciones con avisos recientes')).first.wait_for(timeout=40000)
        cards = page.locator('div.space-y-3 > div.bg-white.rounded-xl > button')
        n = min(10, cards.count())
        for i in range(n):
            cards.nth(i).click()
        page.wait_for_timeout(500)
        page.wait_for_function("() => !document.body.innerText.includes('Analizando compatibilidad')", timeout=60000)
        txt = page.inner_text('body')
        revisadas += n
        if 'Todavía no hay avisos publicados' in txt:
            vacios.append(dni)
    paso(4, 'Perfiles → DEMO-001 → Oportunidades → expandir → badges → modal; top 10 de los 5 DEMO sin avisos vacíos',
         badges and antig and modal_ok and not vacios, f'{shot} + {shot2}',
         f'badges vistos: {badges}, antigüedad: {antig}, encabezado modal "N ofertas · X activas": {modal_ok}, '
         f'ocupaciones revisadas: {revisadas}, perfiles con bloque vacío: {vacios or "ninguno"}', tomar(errs))

    page.goto(f"{BASE}/oficina-empleo/perfiles/futuro?perfil_id={demos['DEMO-001']}", wait_until='networkidle')
    page.get_by_text('soldador/soldadora', exact=True).first.wait_for(timeout=60000)
    page.get_by_text('soldador/soldadora', exact=True).first.click()
    page.get_by_text('Dónde aprender lo que falta').first.wait_for(timeout=40000)
    page.wait_for_function("() => !document.body.innerText.includes('Buscando cursos')", timeout=40000)
    page.wait_for_timeout(2000)
    t5 = page.inner_text('body')
    paneles = {k: (k in t5) for k in ['Lo que ya tiene', 'Lo que necesita aprender', 'Dónde aprender lo que falta', 'Skills transferibles', 'Caminos alternativos']}
    proyectada = bool(re.search(r'→\s*\d+%|compatibilidad', t5, re.I))
    shot = f'{SHOTS}/f4_5_futuro.png'; page.screenshot(path=shot, full_page=True)
    paso(5, 'Futuro laboral DEMO-001: 5 paneles + cursos con compatibilidad proyectada', all(paneles.values()) and proyectada, shot,
         f'paneles: {paneles}, compatibilidad proyectada: {proyectada}', tomar(errs))

    page.goto(f'{BASE}/oficina-empleo/perfiles/nuevo', wait_until='networkidle')
    page.get_by_role('button', name='Tareas').click()
    page.get_by_role('button', name='Relato libre').click()
    page.get_by_placeholder(re.compile('Trabajé 5 años')).fill('trabajé de albañil, levanto paredes y hago revoques')
    page.get_by_role('button', name='Extraer habilidades').click()
    spinner = page.get_by_text('Analizando el relato…').first.is_visible()
    page.get_by_text(re.compile(r'\d+ skills identificadas')).wait_for(timeout=30000)
    t6 = page.locator('div.border.rounded-lg.overflow-hidden').last.inner_text()
    shot = f'{SHOTS}/f4_6_texto_libre.png'; page.screenshot(path=shot, full_page=True)
    paso(6, 'perfiles/nuevo: texto libre albañil', True, shot, f"spinner 'Analizando el relato…': {spinner} | {' · '.join(t6.split(chr(10))[:6])}", tomar(errs))

    paso(7, 'Login OE → /oficina-empleo (redirect por rol)', url7.rstrip('/').endswith('/oficina-empleo'), shot7, url7, errs7)
    ctx.close()
    b.close()

json.dump(resultados, open(f'{SHOTS}/fase4.json', 'w'), ensure_ascii=False, indent=1)
