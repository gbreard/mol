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


class TraductorContexto:
    """Evaluador de reglas de contexto. Fuentes inyectables para test y shadow."""

    def __init__(self, hubs_data: Optional[dict] = None,
                 hubs_activos: Optional[List[str]] = None,
                 exclusiones_trigger: Optional[List[str]] = None,
                 catalogo_codes: Optional[set] = None,
                 lexico: Optional[dict] = None):
        if hubs_data is None:
            hubs_data = json.load(open(REPO / 'docs' / 'MOL_reglas_ESCO_88_ocupaciones_COMPLETO.json'))
        self.hubs = {o['codigo_esco']: o for o in hubs_data['ocupaciones']}
        # overlay del lexico compilado (config/lexico_traductor.json): reemplaza la
        # condicion_operacional de cada regla compilada; la prosa queda intacta.
        if lexico is None:
            lex_path = REPO / 'config' / 'lexico_traductor.json'
            lexico = json.load(open(lex_path)) if lex_path.exists() else {'hubs': {}}
        for cod, reglas_lex in (lexico.get('hubs') or {}).items():
            hub = self.hubs.get(cod)
            if not hub:
                continue
            for r in hub.get('reglas_desambiguacion', []):
                lx = reglas_lex.get(r.get('regla_id'))
                if lx:
                    r['condicion_operacional'] = {**lx, 'campo': 'contenidos'}
                    if lx.get('tecnologia_definitoria'):
                        r['tecnologia_definitoria'] = True
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
        for c in self.activos:
            for t in self.hubs[c].get('titulos_aviso', []):
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
                        inclusion_comparativa: Optional[dict] = None) -> dict:
        """Devuelve {'satisfecha': bool, 'matches': [(termino, campo)], 'estado': ...}."""
        modo = cond.get('modo')
        if not modo or modo not in MODOS_EJECUTABLES:
            return {'satisfecha': False, 'matches': [], 'estado': 'regla_sin_compilar'}
        terminos = cond.get('terminos') or []
        if not terminos:
            return {'satisfecha': False, 'matches': [], 'estado': 'regla_sin_compilar'}

        textos = {c: _norm(contenidos.get(c, '') or '') for c in CAMPOS_CONTENIDOS}

        def _matches_de(terms):
            out = []
            for t in terms:
                for campo, txt in textos.items():
                    if txt and _term_en_texto(t, txt):
                        out.append((t, campo))
                        break  # primer campo que aporta (la traza registra ese campo)
            return out

        matches = _matches_de(terminos)
        # modificador excluye: si aparece un término excluido, la condición NO se satisface
        excluye = cond.get('excluye') or []
        if excluye and _matches_de(excluye):
            return {'satisfecha': False, 'matches': matches, 'estado': 'excluida'}

        n = len({t for t, _ in matches})
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
                nh = len({t for t, _ in _matches_de(h.get('terminos') or [])})
                max_hermana = max(max_hermana, nh)
            ok = propios >= 1 and propios > max_hermana
        else:
            ok = False

        # guarda (a): no satisfecha SOLO por tecnologías/sistemas salvo declaración
        if ok and not tecnologia_definitoria:
            campos_aportantes = {c for _, c in matches}
            if campos_aportantes and campos_aportantes <= CAMPOS_SOLO_TECNOLOGIA:
                return {'satisfecha': False, 'matches': matches,
                        'estado': 'guarda_tecnologia'}
        return {'satisfecha': ok, 'matches': matches, 'estado': 'evaluada'}

    # ── paso 2: secuencia de un hub ──
    def _evaluar_hub(self, codigo: str, contenidos: Dict[str, str]) -> dict:
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

        # a) D en orden
        for r in sorted(hub.get('reglas_desambiguacion', []),
                        key=lambda x: int(x.get('orden', 999))):
            cond = r.get('condicion_operacional') or {}
            res = self._eval_condicion(cond, contenidos, hermanas_de(r.get('regla_id')), _tec_def(r),
                                       inclusion_comparativa=cond_inclusion or None)
            traza_reglas.append({'regla_id': r.get('regla_id'), 'estado': res['estado'],
                                 'satisfecha': res['satisfecha'],
                                 'matches': [{'termino': t, 'campo': c} for t, c in res['matches']]})
            if res['satisfecha']:
                dst = r.get('ocupacion_destino') or {}
                if isinstance(dst, str):
                    m = re.search(r'"codigo_esco":\s*"([\d.]+)"', dst.replace("'", '"'))
                    dst = {'codigo_esco': m.group(1)} if m else {}
                cod_dst = dst.get('codigo_esco')
                if cod_dst and cod_dst in self.catalogo:
                    return {'propone': cod_dst, 'regla_id': r.get('regla_id'),
                            'camino': 'D_directa', 'traza': traza_reglas,
                            'prosa': r.get('condicion_prosa')}
                traza_reglas[-1]['estado'] = 'destino_no_verificado'
        # b) inclusión
        ri = hub.get('regla_inclusion') or {}
        cond = ri.get('condicion_operacional') or {}
        res = self._eval_condicion(cond, contenidos, hermanas_de(None), False)
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
        traza = {'hubs_activados': [], 'titulo_norm': _norm(titulo_limpio)}
        if not candidatos:
            return {'decide': False, 'telemetria': 'no_aplica', 'traza': traza}

        propuestas = []
        for hub_cod, trig in candidatos.items():
            r = self._evaluar_hub(hub_cod, contenidos)
            traza['hubs_activados'].append({
                'hub': hub_cod, 'hub_id': self.hubs[hub_cod]['id'],
                'trigger': trig, 'propone': r['propone'],
                'regla_id': r['regla_id'], 'camino': r['camino'],
                'reglas': r['traza']})
            if r['propone']:
                propuestas.append((hub_cod, r))

        if not propuestas:
            return {'decide': False, 'telemetria': 'familia_sin_rama', 'traza': traza}

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
