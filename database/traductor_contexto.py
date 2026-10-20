"""Traductor de contexto (Eje 4) — evaluador de las reglas consolidadas de Cyn.

FRENTE H, 2026-08-06. Contrato laudado (cruces del harness + re-laudo hub-set):

  1. titulo_limpio → longest-match contra titulos_aviso de los hubs ACTIVOS
     (menos la lista de exclusión de la auditoría de los 76) → hubs candidatos.
  2. Por cada hub candidato, SU secuencia: D01..Dn EN ORDEN (redirigir antes de
     capturar) → primera D satisfecha propone su destino; ninguna → la regla de
     inclusión; tampoco → el hub no propone.
  3. Combinación (vecindario dinámico, local a la oferta):
     - exactamente UNA propuesta → decide (resolución por evidencia)
     - varias con el MISMO destino → decide, camino='convergencia'
     - destinos DISTINTOS → no_forzar + telemetria='evidencia_mixta'
     - ninguna → no_forzar + telemetria='familia_sin_rama'
     (sin hubs activados → telemetria='no_aplica')
  4. Estados de telemetría: no_aplica / familia_sin_rama / evidencia_mixta /
     regla_sin_compilar (por regla, en traza).

Modos ejecutables: alguna · min_matches:k · principalmente (comparativo entre
ramas hermanas; empate NO decide) · solo_estas · modificador excluye.
`evaluacion_semantica_*` NO es ejecutable (laudo D2): la regla está inactiva
(no evalúa, no decide, telemetría regla_sin_compilar).

Campo `contenidos` (laudo D3): tareas_explicitas + skills_habilidades +
conocimientos + tecnologias + sistemas_herramientas, con las dos guardas:
(a) una regla NO se satisface solo por matches en tecnologias/sistemas salvo
    declaración tecnologia_definitoria;
(b) la traza registra QUÉ CAMPO aportó cada match.

Destinos SOLO por esco_code verificado contra el catálogo.
La prosa de Cyn jamás se reescribe: viaja en la traza tal cual.
"""
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional

REPO = Path(__file__).resolve().parent.parent
MODOS_EJECUTABLES = {'alguna', 'min_matches', 'principalmente', 'solo_estas'}
CAMPOS_CONTENIDOS = ['tareas_explicitas', 'skills_habilidades', 'conocimientos',
                     'tecnologias', 'sistemas_herramientas']
CAMPOS_SOLO_TECNOLOGIA = {'tecnologias', 'sistemas_herramientas'}


def _norm(s: str) -> str:
    s = unicodedata.normalize('NFD', (s or '').lower())
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    # PRE-v0.3.3 (paridad de genero, bug — no fase 2): los titulos reales escritos
    # con barra compacta ('vendedor/a', 'ejecutivo/a comercial') deben disparar los
    # mismos triggers que su forma masculina. Se canonicaliza AQUI porque _norm es
    # la funcion compartida de triggers, titulos, exclusiones y terminos (contrato).
    s = re.sub(r'(\w+)/(?:a|na|ra|sa|iz|triz)\b', r'\1', s)
    return re.sub(r'\s+', ' ', s).strip()


def _expandir_genero(lab: str) -> List[str]:
    """'operario/a de X' -> ['operario de X', 'operaria de X'] (sufijos múltiples)."""
    if not re.search(r'\w+/(a|na|ra|sa|iz|triz)\b', lab):
        return [lab]
    masc, fem = lab, lab
    for _ in range(4):
        m = re.search(r'(\w+)/(a|na|ra|sa|iz|triz)\b', masc)
        if not m:
            break
        masc = masc[:m.start()] + m.group(1) + masc[m.end():]
    for _ in range(4):
        m = re.search(r'(\w+)/(a|na|ra|sa|iz|triz)\b', fem)
        if not m:
            break
        base, suf = m.group(1), m.group(2)
        f = base[:-1] + suf if base.endswith(('o', 'e')) else base + suf
        fem = fem[:m.start()] + f + fem[m.end():]
    return [masc, fem]


def _term_en_texto(termino: str, texto_norm: str) -> bool:
    """Match con límites de palabra sobre texto normalizado."""
    t = _norm(termino)
    if not t:
        return False
    return re.search(r'(?<!\w)' + re.escape(t) + r'(?!\w)', texto_norm) is not None


# ── CAPA DE EQUIVALENCIA FUNCIONAL (mini-frente árbol v12.5) ──────────────────
# NO re-escribe las condiciones (prosa compilada de Cyn): normaliza AMBOS lados
# (término de condición y tarea) a su verbo-núcleo para que la nominalización de v11
# ("arqueo", "carga de facturas", "asesoramiento") matchee la verbalización de v12.5
# ("arquear", "cargar facturas", "asesorar") — doctrina de equivalencia funcional de Cyn.
# Se usa SOLO como fallback cuando el match exacto falla → solo puede AGREGAR matches,
# nunca quitar (estables y cobertura nueva quedan intactas).
_EQ_STOP = frozenset('de la el los las un una unos unas y o u en con para por a al del que se su '
                     'sus como sobre entre segun e cada todo toda todos las lo le les mediante '
                     'segun ante tras hacia desde sin'.split())
# irregulares: nominalización y verbo → token compartido (diptongos / raíces que el
# stemmer regular no alinea).
# irregulares acotados a nominalización↔verbo de TAREA (no transaccionales genéricos como
# venta/pago/cobro/compra — demasiado frecuentes → sobre-disparan). Solo los que alinean
# diptongos/raíces de acciones específicas.
_EQ_IRREG = {
    'cierre': 'cerr', 'cerrar': 'cerr', 'cierres': 'cerr',
    'atencion': 'aten', 'atender': 'aten', 'atiende': 'aten',
    'reposicion': 'repo', 'reponer': 'repo', 'repone': 'repo', 'repos': 'repo',
    'arqueo': 'arque', 'arquear': 'arque',
}
_EQ_SUF = ('amientos', 'amiento', 'imientos', 'imiento', 'aciones', 'acion', 'iciones', 'icion',
           'ciones', 'cion', 'siones', 'sion', 'adores', 'ador', 'adoras', 'adora', 'ados',
           'adas', 'ado', 'ada', 'idos', 'idas', 'ido', 'ida', 'ajes', 'aje', 'ando', 'iendo',
           'ar', 'er', 'ir', 'os', 'as', 'es', 'o', 'a', 'e')


def _eq_stem(w: str) -> str:
    if w in _EQ_IRREG:
        return _EQ_IRREG[w]
    for suf in _EQ_SUF:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[:-len(suf)]
    return w


def _eq_stems(texto_norm: str) -> set:
    return {_eq_stem(w) for w in texto_norm.split() if w not in _EQ_STOP and len(w) > 2}


def _eq_seq(texto_norm: str) -> list:
    return [_eq_stem(w) for w in texto_norm.split() if w not in _EQ_STOP and len(w) > 2]


def _term_equiv_en_texto(termino: str, texto_norm: str) -> bool:
    """Equivalencia funcional ESTRICTA (verbo-núcleo+objeto): las raíces de contenido del
    término deben aparecer como SUBSECUENCIA CONTIGUA (frase) en el texto — no dispersas.
    'cierre de caja'→[cerr,caj] ⊂ 'cerrar caja'; evita falsos por tokens sueltos.
    Para términos de UNA sola palabra exige raíz específica (≥5) para no sobre-disparar
    genéricos cortos (vend/pag/cobr/arm/carg)."""
    tn = _norm(termino)
    ts = [_eq_stem(w) for w in tn.split() if w not in _EQ_STOP and len(w) > 2]
    if not ts:
        return False
    if len(ts) == 1 and len(ts[0]) < 5:
        return False  # mono-token genérico corto: no rescatar (lo cubre el match exacto)
    seq = _eq_seq(texto_norm)
    n = len(ts)
    for i in range(len(seq) - n + 1):
        if seq[i:i + n] == ts:
            return True
    return False


# ── LAUDO CYN 2026-10-19 — términos que NO acreditan núcleo funcional ──────────
# LAUDO 1 (hoja 1 «1-cajeros», D4/A20): el predominio se mide por el NÚCLEO FUNCIONAL,
# no por la cantidad de tareas. "Atención al cliente es tarea complementaria y no demuestra
# actividad de venta." Las complementarias (atención/soporte/identificar-necesidades/
# delivery/asistencia) NO cuentan para NINGÚN lado del comparativo ni para min_matches.
# LAUDO 2 (Excel D10, C17/C63): la ATENCIÓN TELEFÓNICA no acredita televenta — D10 exige
# promoción/venta por llamada. Estos términos tampoco cuentan para el núcleo.
# Solo se excluyen con los ajustes del mini-frente ON (self._equiv); OFF → producción intacta.
# Complementarias (atención/soporte). La exclusión se ACOTA al contexto caja/venta
# (hubs en _NUCLEO_SCOPED) — global rompía costo en otros hubs donde la atención es core.
_NO_NUCLEO = {
    'atencion al cliente', 'atencion al publico', 'atender clientes', 'atiende clientes',
    'atender compradores', 'atender al cliente', 'atender al publico', 'identificar necesidades',
    'identifica necesidades', 'informar sobre productos', 'informa productos', 'informar a clientes',
    'responder consultas', 'responde consultas', 'delivery', 'asistencia', 'brindar asistencia', 'asistir',
}
# hubs donde rige el deslinde núcleo-funcional de Cyn (caja vs venta). Fuera de acá, la
# atención puede ser núcleo legítimo → no se excluye.
_NUCLEO_SCOPED = {'5223.4', '5230.1'}
# LAUDO 2 (D10): términos de ATENCIÓN telefónica que NO acreditan televenta (C63) vs los que SÍ.
_D10_ATENCION_TEL = {'por telefono', 'llamadas telefonicas', 'llamadas entrantes', 'contacto telefonico',
                     'atencion telefonica', 'atender telefonicamente', 'responder llamadas'}
_D10_TELEVENTA = {'venta telefonica', 'ventas telefonicas', 'televentas', 'telemarketing',
                  'cierre telefonico', 'venta remota', 'canales remotos', 'call center', 'llamadas salientes'}

# ── LAUDO 3 (hoja 2 «2-lenguaje comercial», C12-E10) — equivalencias comerciales con MATIZ ──
# Cyn: equivalencia solo si MISMA función (acción+objeto+finalidad+alcance+nivel). "La equivalencia
# aceptada es EVIDENCIA para evaluar, nunca clasificación automática" (C28). Cada término de condición
# acepta ciertas reformulaciones de v12.5 y RECHAZA otras (acotación textual). acepta → cuenta como
# match; las frases rechazadas NO cuentan. Solo con el mini-frente ON (self._equiv).
_SINONIMOS_COMERCIALES = {
    'prospeccion': {'acepta': ['captar nuevos clientes', 'captar clientes', 'generar nuevos clientes',
                               'captacion de nuevos clientes', 'captacion de clientes', 'detectar y abrir oportunidades',
                               'abrir nuevas oportunidades', 'abrir oportunidades'],
                    'rechaza': ['identificar oportunidades']},  # parcial — no acredita captación
    'fidelizar': {'acepta': ['conservar relaciones', 'fortalecer relaciones', 'dar continuidad a',
                             'fidelizar', 'fidelizacion', 'retener clientes', 'retencion de clientes'],
                  'rechaza': ['gestionar cartera', 'desarrollar cartera', 'ampliar cartera']},
    'desarrollar relaciones comerciales': {'acepta': ['construir relaciones', 'fortalecer relaciones',
                             'expandir relaciones', 'establecer relaciones comerciales'],
                  'rechaza': ['gestion de clientes', 'gestionar clientes']},
    'comercializar': {'acepta': ['promocionar y vender', 'promocionar y comercializar', 'vender productos',
                             'venta consultiva', 'comercializar'],
                  'rechaza': ['posicionar portfolio', 'posicionar el portfolio']},
    'negociacion': {'acepta': ['negociar contratos', 'negociar condiciones', 'negociacion y cierre',
                             'proceso de negociacion', 'negociar y cerrar'],
                  'rechaza': []},  # el cierre aislado NO acredita negociación (se maneja por ausencia en acepta)
    'establecer objetivos': {'acepta': [],   # NO equivale (cumplir/alcanzar ≠ establecer)
                  'rechaza': ['cumplir objetivos', 'alcanzar objetivos', 'cumplir con los objetivos']},
    'cotizaciones': {'acepta': ['emitir presupuestos', 'elaborar presupuestos', 'propuestas de precios',
                             'cotizar', 'realizar cotizaciones', 'presupuestar'],
                  'rechaza': ['facturacion', 'notas de credito', 'notas de debito']},
    'rutas': {'acepta': ['visitas segun itinerario', 'recorridos segun itinerario', 'ejecutar visitas',
                             'visitas presenciales segun', 'recorrer la zona'],
                  'rechaza': ['disenar rutas', 'planificar rutas']},
}


# R1 (micro-fix, laudo C17): TELEVENTA DEMOSTRADA = venta/promoción LIGADA a la llamada
# (verbo de venta cerca del marcador telefónico, en la misma tarea). Distingue "llamadas PARA
# vender" (televenta → D10) de "atiende por teléfono + vende presencial" (vendedor, p.ej. gomería).
# La lista negativa C63 (atención/consultas/responder/informar) NO trae verbo de venta ligado →
# NO dispara. Equivalencia funcional dentro de C17, no reescritura de la condición.
_TELEVENTA_TERMS = {'venta telefonica', 'ventas telefonicas', 'televentas', 'telemarketing',
                    'cierre telefonico', 'venta remota'}
# La venta debe estar LIGADA a la llamada (C17 "mediante llamadas"), no mera co-ocurrencia:
# (a) "llamadas comerciales/de venta"; (b) "llamadas … PARA/mediante vender/ofrecer/…";
# (c) frases exactas de televenta. NO dispara con "atiende por teléfono" + venta presencial
# en tareas distintas (p.ej. gomería) — ésas no tienen el nexo.
_TELEVENTA_RE = re.compile(
    r'llamad\w*\s+(comercial\w*|de venta|para vender)'
    r'|(llamad\w*|telefon\w*|por telefono)[^.;]{0,30}\b(para|mediante|a fin de)\b[^.;]{0,25}'
    r'(vend\w*|venta|ofrec\w*|promocion\w*|captar|comercializ\w*|coloca\w*)'
    r'|\bvent\w*\s+(telefonic\w*|remot\w*)|televent\w*|telemarketing|cierre telefonic\w*'
    r'|(vender|venta|ventas|cerrar vent\w*)\s+(por telefono|telefonic\w*|remot\w*)',
    re.IGNORECASE)


def _televenta_demostrada(texto_norm: str) -> bool:
    return bool(_TELEVENTA_RE.search(texto_norm))


def _sinonimo_comercial_en_texto(termino: str, texto_norm: str) -> bool:
    """LAUDO 3 + R1: el término de condición matchea si el texto trae una reformulación ACEPTADA
    por Cyn (acción equivalente). Para los términos de televenta (D10), acepta la televenta
    DEMOSTRADA (venta ligada a la llamada). Las rechazadas/parciales y la atención no cuentan."""
    tn = _norm(termino)
    if tn in _TELEVENTA_TERMS:
        return _televenta_demostrada(texto_norm)
    fam = _SINONIMOS_COMERCIALES.get(tn)
    if not fam:
        return False
    return any(_norm(a) in texto_norm for a in fam['acepta'])


class TraductorContexto:
    """Evaluador de reglas de contexto. Fuentes inyectables para test y shadow."""

    def __init__(self, hubs_data: Optional[dict] = None,
                 hubs_activos: Optional[List[str]] = None,
                 exclusiones_trigger: Optional[List[str]] = None,
                 catalogo_codes: Optional[set] = None,
                 lexico: Optional[dict] = None,
                 satelites: Optional[Dict[str, str]] = None,
                 equivalencia_funcional: bool = False):
        # mini-frente árbol v12.5: capa de equivalencia funcional (nominalización↔verbo)
        # como FALLBACK del match condición↔tarea. OFF por defecto (producción intacta).
        self._equiv = equivalencia_funcional
        # v0.3.3 (laudo P1): mapa label_normalizado -> codigo del satelite.
        # Si el TITULO ENTERO == label de un satelite, rige el modo satelite-exacto.
        self.satelites = satelites or {}
        if hubs_data is None:
            hubs_data = json.load(open(REPO / 'docs' / 'MOL_reglas_ESCO_88_ocupaciones_COMPLETO.json'))
        self.hubs = {o['codigo_esco']: o for o in hubs_data['ocupaciones']}
        # overlay del lexico compilado (config/lexico_traductor.json): reemplaza la
        # condicion_operacional de cada regla compilada; la prosa queda intacta.
        if lexico is None:
            lex_path = REPO / 'config' / 'lexico_traductor.json'
            lexico = json.load(open(lex_path)) if lex_path.exists() else {'hubs': {}}
        # v0.3.4 (laudo A1-bis): term-sets nombrados, referenciados por *_ref.
        # La resolucion asigna EL MISMO OBJETO lista a cada referencia (identidad
        # verificable por test — si pudieran driftear, driftean).
        self._term_sets = {k: v.get('terminos') or []
                           for k, v in (lexico.get('term_sets') or {}).items()}

        def _resolver_refs(lx: dict) -> dict:
            out = {**lx, 'campo': 'contenidos'}
            if 'terminos_ref' in out:
                out['terminos'] = self._term_sets[out['terminos_ref']]
            if 'excluye_ref' in out:
                out['excluye'] = self._term_sets[out['excluye_ref']]
            return out

        for cod, reglas_lex in (lexico.get('hubs') or {}).items():
            hub = self.hubs.get(cod)
            if not hub:
                continue
            ids_hub = {r.get('regla_id') for r in hub.get('reglas_desambiguacion', [])}
            for r in hub.get('reglas_desambiguacion', []):
                lx = reglas_lex.get(r.get('regla_id'))
                if lx:
                    r['condicion_operacional'] = _resolver_refs(lx)
                    if lx.get('tecnologia_definitoria'):
                        r['tecnologia_definitoria'] = True
            # v0.4.0 (K3 P4): ramas EXTRA compiladas prosa-directa desde el lexico
            # (regla_id 'DX_*' con 'destino'): se APPENDEAN como D nuevas — la
            # fuente formal (JSON 2.0 de JD) las incorpora despues; el lexico
            # lleva la prosa de Cyn citada y el tag de telemetria.
            for rid_lex, lx in reglas_lex.items():
                if (rid_lex.startswith('DX_') and rid_lex not in ids_hub
                        and isinstance(lx, dict) and lx.get('destino')):
                    hub.setdefault('reglas_desambiguacion', []).append({
                        'regla_id': rid_lex,
                        'orden': lx.get('orden', 900),
                        'condicion_prosa': lx.get('prosa_cyn', ''),
                        'condicion_operacional': _resolver_refs(lx),
                        'ocupacion_destino': {'codigo_esco': lx['destino']},
                    })
            lx_inc = reglas_lex.get('inclusion')
            if lx_inc:
                hub.setdefault('regla_inclusion', {})['condicion_operacional'] = {**lx_inc, 'campo': 'contenidos'}
        if hubs_activos is None:
            cfg = json.load(open(REPO / 'config' / 'hubs_activos.json'))
            hubs_activos = [h['codigo_esco'] for hs in cfg['hub_sets']
                            if hs.get('estado') == 'activo' for h in hs['hubs']]
        self.activos = [c for c in hubs_activos if c in self.hubs]
        self.exclusiones = {_norm(x) for x in (exclusiones_trigger or [])}
        if catalogo_codes is None:
            meta = json.load(open(REPO / 'database' / 'embeddings' / 'esco_occupations_metadata.json'))
            catalogo_codes = {o['esco_code'] for o in meta if o.get('esco_code')}
            self._code_label = {o['esco_code']: o['esco_label'] for o in meta if o.get('esco_code')}
        else:
            self._code_label = {}
        self.catalogo = catalogo_codes
        # índice de triggers normalizados por hub activo
        self._triggers = []  # (trigger_norm, codigo_hub)
        # v0.4.0 (K3 P4, r1): titulos_aviso_extra declarados en hubs_activos.json
        # (marca fuente_pendiente_jd — la fuente formal es el JSON 2.0; el extra
        # activa el trigger local hasta que JD lo incorpore).
        extras = {}
        try:
            _cfg_ha = json.load(open(REPO / 'config' / 'hubs_activos.json'))
            for _hs in _cfg_ha.get('hub_sets', []):
                for _h in _hs.get('hubs', []):
                    if _h.get('titulos_aviso_extra'):
                        extras[_h['codigo_esco']] = list(_h['titulos_aviso_extra'])
        except Exception:
            pass
        for c in self.activos:
            for t in self.hubs[c].get('titulos_aviso', []) + extras.get(c, []):
                for forma in _expandir_genero(t):
                    tn = _norm(forma)
                    if tn and tn not in self.exclusiones:
                        self._triggers.append((tn, c))

    # ── paso 1: trigger ──
    def _hubs_candidatos(self, titulo_limpio: str) -> Dict[str, str]:
        """longest-match: por hub, el trigger más largo contenido en el título."""
        tn = _norm(titulo_limpio)
        por_hub = {}
        for trig, hub in self._triggers:
            if re.search(r'(?<!\w)' + re.escape(trig) + r'(?!\w)', tn):
                if hub not in por_hub or len(trig) > len(por_hub[hub]):
                    por_hub[hub] = trig
        return por_hub

    # ── evaluación de una condición operacional ──
    def _eval_condicion(self, cond: dict, contenidos: Dict[str, str],
                        hermanas: List[dict], tecnologia_definitoria: bool,
                        inclusion_comparativa: Optional[dict] = None,
                        hub_cod: Optional[str] = None) -> dict:
        """Devuelve {'satisfecha': bool, 'matches': [(termino, campo)], 'estado': ...}."""
        modo = cond.get('modo')
        if not modo or modo not in MODOS_EJECUTABLES:
            return {'satisfecha': False, 'matches': [], 'estado': 'regla_sin_compilar'}
        terminos = cond.get('terminos') or []
        if not terminos:
            return {'satisfecha': False, 'matches': [], 'estado': 'regla_sin_compilar'}

        textos = {c: _norm(contenidos.get(c, '') or '') for c in CAMPOS_CONTENIDOS}

        via_capa = set()  # términos que matchearon SOLO vía capa de equivalencia (no exacto)

        def _matches_de(terms):
            out = []
            for t in terms:
                for campo, txt in textos.items():
                    if not txt:
                        continue
                    if _term_en_texto(t, txt):
                        out.append((t, campo)); break
                    if self._equiv and _term_equiv_en_texto(t, txt):
                        out.append((t, campo)); via_capa.add(t); break
                    if self._equiv and _sinonimo_comercial_en_texto(t, txt):  # LAUDO 3
                        out.append((t, campo)); via_capa.add(t); break
            return out

        matches = _matches_de(terminos)
        # modificador excluye: si aparece un término excluido, la condición NO se satisface.
        # v0.3.4: si el excluye viene de un term-set con tag, la traza lleva el tag.
        excluye = cond.get('excluye') or []
        if excluye and _matches_de(excluye):
            estado = cond.get('excluye_tag') or 'excluida'
            return {'satisfecha': False, 'matches': matches, 'estado': estado}

        # LAUDO 1/2 (núcleo funcional): las complementarias y la atención telefónica NO cuentan
        # para el predominio ni para min_matches (solo con los ajustes del mini-frente ON).
        def _ncore(ms):
            terms = {t for t, _ in ms}
            if self._equiv and hub_cod in _NUCLEO_SCOPED:   # LAUDO 1 acotado al contexto caja/venta
                terms = terms - _NO_NUCLEO
            return len(terms)

        n = _ncore(matches)
        if modo == 'alguna':
            ok = n >= 1
        elif modo == 'min_matches':
            ok = n >= int(cond.get('minimo', 2))
        elif modo == 'solo_estas':
            # debe haber matches y NO aparecer contenidos de las hermanas
            otros = []
            for h in hermanas:
                otros += (h.get('terminos') or [])
            ok = n >= 1 and not _matches_de(otros)
        elif modo == 'principalmente':
            # comparativo entre ramas hermanas; empate NO decide.
            # LAUDO L1: la INCLUSION del hub participa del comparativo.
            propios = n
            max_hermana = 0
            comparadas = list(hermanas)
            if inclusion_comparativa:
                comparadas.append(inclusion_comparativa)
            for h in comparadas:
                nh = _ncore(_matches_de(h.get('terminos') or []))  # LAUDO 1: núcleo, sin complementarias
                max_hermana = max(max_hermana, nh)
            ok = propios >= 1 and propios > max_hermana
        else:
            ok = False

        # guarda (a): no satisfecha SOLO por tecnologías/sistemas salvo declaración
        if ok and not tecnologia_definitoria:
            campos_aportantes = {c for _, c in matches}
            if campos_aportantes and campos_aportantes <= CAMPOS_SOLO_TECNOLOGIA:
                return {'satisfecha': False, 'matches': matches,
                        'estado': 'guarda_tecnologia', 'via_capa': via_capa}
        return {'satisfecha': ok, 'matches': matches, 'estado': 'evaluada', 'via_capa': via_capa}

    def _conteo_matches(self, cond: dict, contenidos: Dict[str, str]) -> int:
        """Terminos DISTINTOS de la condicion presentes en los contenidos (para guards)."""
        terminos = (cond or {}).get('terminos') or []
        if not terminos:
            return 0
        textos = {c: _norm(contenidos.get(c, '') or '') for c in CAMPOS_CONTENIDOS}
        n = 0
        for t in terminos:
            if any(txt and _term_en_texto(t, txt) for txt in textos.values()):
                n += 1
        return n

    # ── paso 2: secuencia de un hub ──
    def _evaluar_hub(self, codigo: str, contenidos: Dict[str, str],
                     sat_code: Optional[str] = None) -> dict:
        hub = self.hubs[codigo]
        traza_reglas = []
        # LAUDO L1 (H_v032, 2026-08-14): para las D redirectoras el conjunto de
        # comparacion del MODO COMPARATIVO (principalmente) = D-hermanas ∪
        # {INCLUSION del hub}. "consiste principalmente en" es predominio sobre
        # TODO, incluido el nucleo del hub: si la inclusion domina el conteo,
        # ninguna D redirige — se evalua la inclusion. Solo el comparativo:
        # solo_estas/min_matches no cambian (letra del laudo).
        cond_inclusion = (hub.get('regla_inclusion') or {}).get('condicion_operacional') or {}
        hermanas_de = lambda excluir_id: [
            (r.get('condicion_operacional') or {})
            for r in hub.get('reglas_desambiguacion', [])
            if r.get('regla_id') != excluir_id]

        def _tec_def(regla):
            comp = regla.get('compilacion') or {}
            return bool(regla.get('tecnologia_definitoria') or comp.get('tecnologia_definitoria'))

        # guard P2a (laudo v0.3.3): hits distintos de la inclusion en ESTA oferta.
        # "Inclusion en 0 hits" presupone inclusion COMPILADA: sin terminos de
        # inclusion no hay cero, hay ausencia — el guard no aplica.
        incl_compilada = bool((cond_inclusion or {}).get('terminos'))
        n_incl = self._conteo_matches(cond_inclusion, contenidos) if incl_compilada else None

        # a) D en orden. v0.3.4 (laudo A2): en modo satelite-exacto, las D cuyo
        # destino COINCIDE con el satelite (confirmatorias) van PRIMERO; el
        # orden interno de cada grupo sigue siendo el de la prosa.
        def _dst_de(rr):
            dst = rr.get('ocupacion_destino') or {}
            if isinstance(dst, str):
                m = re.search(r'"codigo_esco":\s*"([\d.]+)"', dst.replace("'", '"'))
                return m.group(1) if m else None
            return dst.get('codigo_esco')

        if sat_code:
            orden_d = sorted(hub.get('reglas_desambiguacion', []),
                             key=lambda x: (0 if _dst_de(x) == sat_code else 1,
                                            int(x.get('orden', 999))))
        else:
            orden_d = sorted(hub.get('reglas_desambiguacion', []),
                             key=lambda x: int(x.get('orden', 999)))
        for r in orden_d:
            cond = r.get('condicion_operacional') or {}
            res = self._eval_condicion(cond, contenidos, hermanas_de(r.get('regla_id')), _tec_def(r),
                                       inclusion_comparativa=(cond_inclusion or None) if not sat_code else None,
                                       hub_cod=codigo)
            traza_reglas.append({'regla_id': r.get('regla_id'), 'estado': res['estado'],
                                 'satisfecha': res['satisfecha'],
                                 'matches': [{'termino': t, 'campo': c} for t, c in res['matches']]})
            if res['satisfecha']:
                dst = r.get('ocupacion_destino') or {}
                if isinstance(dst, str):
                    m = re.search(r'"codigo_esco":\s*"([\d.]+)"', dst.replace("'", '"'))
                    dst = {'codigo_esco': m.group(1)} if m else {}
                cod_dst = dst.get('codigo_esco')
                n_hits = len({t for t, _ in res['matches']})
                # GUARD mini-frente (laudo harness): un redirect D cuyo soporte ENTERO es un
                # solo CONCEPTO (una raíz; las variantes singular/plural cuentan como uno) que
                # matcheó SOLO vía capa de equivalencia NO puede disparar el redirect — exige
                # un 2º término de apoyo de OTRA raíz (directo o vía capa). Evita el falso
                # cruza-dominio (showroom→seguros: "aseguradoras" matcheó "asegurar embalaje"
                # por la raíz "asegur"). Solo con capa ON; OFF→via vacío (producción intacta).
                via = res.get('via_capa') or set()
                _mt = {t for t, _ in res['matches']}
                _raices = {_eq_stem(next((w for w in _norm(t).split()
                                          if w not in _EQ_STOP and len(w) > 2), _norm(t)))
                           for t in _mt}
                if self._equiv and cod_dst and _mt and _mt <= via and len(_raices) == 1:
                    traza_reglas[-1]['estado'] = 'guard_capa_concepto_unico'
                    continue
                # GUARD D10 (laudo 2, C17/C63): teleoperador (5244.1) NO dispara por mera
                # atención telefónica — exige un término de TELEVENTA (promoción/venta por
                # llamada). Si los matches son solo atención-telefónica → no cruza.
                if (self._equiv and cod_dst == '5244.1'
                        and not (_mt & _D10_TELEVENTA)
                        and (_mt & _D10_ATENCION_TEL)):
                    traza_reglas[-1]['estado'] = 'guard_d10_atencion_no_televenta'
                    continue
                if sat_code:
                    # regla de interaccion P1xP2 (laudada): destino == satelite del
                    # titulo -> redirect confirmatorio con 1 hit; OTRO destino ->
                    # exige >=2 hits en terminos distintos.
                    if cod_dst != sat_code and n_hits < 2:
                        traza_reglas[-1]['estado'] = 'satelite_d_contraria_insuficiente'
                        continue
                else:
                    # guard P2a: inclusion COMPILADA en 0 -> la D necesita >=2 terminos distintos.
                    # v0.4.0 (K3 P4 r3): las ramas canal-remoto llevan guard_exento en el
                    # lexico — laudo posterior y especifico precede al guard generico.
                    if n_incl == 0 and n_hits < 2 and not cond.get('guard_exento'):
                        traza_reglas[-1]['estado'] = 'guard_1a0_bloqueo'
                        continue
                if cod_dst and cod_dst in self.catalogo:
                    return {'propone': cod_dst, 'regla_id': r.get('regla_id'),
                            'camino': 'D_directa', 'traza': traza_reglas,
                            'prosa': r.get('condicion_prosa')}
                traza_reglas[-1]['estado'] = 'destino_no_verificado'
        # b) inclusión — en modo satelite-exacto NO participa (laudo P1)
        if sat_code:
            traza_reglas.append({'regla_id': 'inclusion', 'estado': 'satelite_exacto_no_participa',
                                 'satisfecha': False, 'matches': []})
            return {'propone': None, 'regla_id': None, 'camino': None, 'traza': traza_reglas}
        ri = hub.get('regla_inclusion') or {}
        cond = ri.get('condicion_operacional') or {}
        res = self._eval_condicion(cond, contenidos, hermanas_de(None), False, hub_cod=codigo)
        traza_reglas.append({'regla_id': 'inclusion', 'estado': res['estado'],
                             'satisfecha': res['satisfecha'],
                             'matches': [{'termino': t, 'campo': c} for t, c in res['matches']]})
        if res['satisfecha'] and codigo in self.catalogo:
            return {'propone': codigo, 'regla_id': 'inclusion', 'camino': 'inclusion',
                    'traza': traza_reglas, 'prosa': ri.get('condicion_prosa')}
        # c) nada
        return {'propone': None, 'regla_id': None, 'camino': None, 'traza': traza_reglas}

    # ── pasos 1-4: evaluación completa de una oferta ──
    def evaluar(self, titulo_limpio: str, contenidos: Dict[str, str]) -> dict:
        """Evalúa una oferta. contenidos: dict con los 5 campos (str cada uno).

        Devuelve: {decide: bool, codigo_esco, hub_id, regla_id, camino,
                   telemetria, traza}
        """
        candidatos = self._hubs_candidatos(titulo_limpio)
        tn = _norm(titulo_limpio)
        sat_code = self.satelites.get(tn)  # v0.3.3 P1: titulo ENTERO == label de satelite
        traza = {'hubs_activados': [], 'titulo_norm': tn}
        if sat_code:
            traza['satelite_exacto'] = sat_code
        if not candidatos:
            return {'decide': False, 'telemetria': 'no_aplica', 'traza': traza}

        propuestas = []
        for hub_cod, trig in candidatos.items():
            r = self._evaluar_hub(hub_cod, contenidos, sat_code=sat_code)
            traza['hubs_activados'].append({
                'hub': hub_cod, 'hub_id': self.hubs[hub_cod]['id'],
                'trigger': trig, 'propone': r['propone'],
                'regla_id': r['regla_id'], 'camino': r['camino'],
                'reglas': r['traza']})
            if r['propone']:
                propuestas.append((hub_cod, r))

        if not propuestas:
            if sat_code:
                # laudo P1: abstencion con tag propio — el destino final aguas-abajo
                # lo registra el shadow/pipeline (este modulo no conoce los canales).
                return {'decide': False, 'telemetria': 'satelite_exacto_abstencion',
                        'satelite': sat_code, 'traza': traza}
            tele = 'familia_sin_rama'
            if any(reg.get('estado') == 'guard_1a0_bloqueo'
                   for h in traza['hubs_activados'] for reg in h['reglas']):
                traza['tag_guard_1a0'] = True
            return {'decide': False, 'telemetria': tele, 'traza': traza}

        destinos = {r['propone'] for _, r in propuestas}
        if len(destinos) == 1:
            destino = destinos.pop()
            hub_cod, r = propuestas[0]
            camino = 'convergencia' if len(propuestas) > 1 else r['camino']
            return {'decide': True, 'codigo_esco': destino,
                    'esco_label': self._code_label.get(destino),
                    'hub_id': self.hubs[hub_cod]['id'], 'regla_id': r['regla_id'],
                    'camino': camino, 'telemetria': 'decidido', 'traza': traza}
        traza['destinos_en_conflicto'] = sorted(destinos)
        return {'decide': False, 'telemetria': 'evidencia_mixta', 'traza': traza}
