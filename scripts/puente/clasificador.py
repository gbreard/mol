"""
Clasificador de candidatas del puente validacion->diccionario (mesa de Cyn, Eje 4).

Separa correcciones de ocupacion en:
  - VOCABULARIO: denominacion estable, un destino ESCO plausible -> diccionario plano.
  - CONDICIONAL: destino depende de tareas -> evidencia para el traductor del Eje 4.
  - RUIDO: titulo que no es denominacion (empresa, localidad, ruido NLP).

Config CONGELADA en config/clasificador_candidatas.json. Validado en seco (FRENTE B v2):
0 falsos vocabulario sobre 34 casos. NO validado out-of-sample.

Orden de senales: S1(familia) -> S1b(dict-contextos) -> S3(conflicto) -> guard-prof -> S2(forma) -> VOCABULARIO.
"""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "clasificador_candidatas.json"
DICT_PATH = ROOT / "config" / "sinonimos_argentinos_esco.json"


def _norm(s):
    s = (s or "").lower().strip()
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


class Clasificador:
    """Clasificador de candidatas. Lee la config congelada y el diccionario
    (para la senal S1b dinamica)."""

    def __init__(self, config_path=None, dict_path=None):
        self.config = json.loads(Path(config_path or CONFIG_PATH).read_text(encoding="utf-8"))
        self._dict_path = Path(dict_path or DICT_PATH)
        self._compile()

    def _compile(self):
        c = self.config
        self.familias_azules = c["familias_azules"]["raices"]
        self.familias_blancas = c["familias_blancas"]["raices"]
        self.guard_min_puntos = c["guard_profundidad"]["min_puntos"]
        self.conectores_corte = c["criterio_head"]["conectores_corte"]
        self.separadores_corte = c["criterio_head"]["separadores_corte"]
        self.prefijo_ruido = re.compile(c["criterio_head"]["prefijos_ruido_regex"], re.I)
        self.prefijo_localidad = re.compile(c["criterio_head"]["prefijo_localidad_regex"], re.I)
        self.s2_conectores = c["s2_conectores_forma"]
        # regex de raiz por familia: raiz + o/a opcional + /a|/o opcional
        self._fam_az = [(f, self._raiz_regex(f)) for f in self.familias_azules]
        self._fam_bl = [(f, self._raiz_regex(f)) for f in self.familias_blancas]
        # S1b dinamico: entradas del diccionario con bloque contextos
        self.dict_contextos = self._load_dict_contextos()

    @staticmethod
    def _raiz_regex(fam):
        base = fam[:-1] if fam.endswith("o") else fam
        return re.compile(r"^(?:" + re.escape(base) + r"[oa]?(?:/a|/o)?)\b")

    def _load_dict_contextos(self):
        try:
            dic = json.loads(self._dict_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return []
        entries = {k: v for k, v in dic.get("ocupaciones_titulo", {}).items()
                   if not k.startswith("_")}
        return sorted({_norm(k) for k, v in entries.items() if v.get("contextos")})

    # ---- head de la denominacion ----
    def head(self, denom):
        n = _norm(denom)
        n = self.prefijo_ruido.sub("", n)
        n = self.prefijo_localidad.sub("", n)
        # cortar en el primer conector o separador
        conect = r"\b(?:" + "|".join(re.escape(x) for x in self.conectores_corte) + r")\b"
        seps = "|".join(re.escape(x) for x in self.separadores_corte)
        n = re.split(conect + r"|" + seps, n)[0].strip()
        return n

    # ---- senales ----
    def s1(self, denom):
        h = self.head(denom)
        for fam, rx in self._fam_az:
            if rx.match(h):
                return ("azul", fam)
        for fam, rx in self._fam_bl:
            if rx.match(h):
                return ("blanca", fam)
        return None

    def s1b(self, denom):
        h = self.head(denom)
        for dc in self.dict_contextos:
            if h == dc or re.match(r"^" + re.escape(dc) + r"\b", h):
                return dc
        return None

    def s2(self, denom):
        n = self.prefijo_ruido.sub("", _norm(denom))
        for q in self.s2_conectores:
            if q in n:
                return q.strip()
        return None

    def guard_profundidad(self, esco_code):
        return (esco_code or "").count(".") >= self.guard_min_puntos

    def s3_conflicto(self, denom, esco_code, dict_lookup=None):
        """Conflicto retroactivo: el head ya existe en el diccionario con OTRO esco_code.
        dict_lookup: dict {denom_norm: esco_code} construido por el sugeridor. Si None,
        se construye desde el diccionario (solo entradas con esco_code)."""
        if dict_lookup is None:
            dict_lookup = self._dict_esco_codes()
        n = _norm(denom)
        for dk, dcode in dict_lookup.items():
            if len(dk) >= 4 and re.search(r"\b" + re.escape(dk) + r"\b", n):
                if dcode and dcode != esco_code:
                    return {"denominacion_dic": dk, "esco_code_dic": dcode,
                            "esco_code_correccion": esco_code}
        return None

    def _dict_esco_codes(self):
        try:
            dic = json.loads(self._dict_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        out = {}
        for k, v in dic.get("ocupaciones_titulo", {}).items():
            if k.startswith("_"):
                continue
            code = v.get("esco_code")
            if code:
                out[_norm(k)] = code
                for var in v.get("variantes", []):
                    out.setdefault(_norm(var), code)
        return out

    # ---- clasificacion ----
    def clasificar(self, denom, esco_code, dict_lookup=None):
        """Devuelve dict {clase, senal, detalle, conflicto_retroactivo}."""
        r1 = self.s1(denom)
        if r1:
            return self._res("CONDICIONAL", f"S1-{r1[0]}:{r1[1]}")
        r1b = self.s1b(denom)
        if r1b:
            return self._res("CONDICIONAL", f"S1b-dict:{r1b}")
        r3 = self.s3_conflicto(denom, esco_code, dict_lookup)
        if r3:
            return self._res("CONDICIONAL", "S3-conflicto", conflicto=r3)
        if self.guard_profundidad(esco_code):
            n = esco_code.count(".")
            return self._res("CONDICIONAL", f"guard-prof:{n}pts")
        r2 = self.s2(denom)
        if r2:
            return self._res("CONDICIONAL", f"S2-forma:{r2}")
        return self._res("VOCABULARIO", "sin-senal")

    @staticmethod
    def _res(clase, senal, conflicto=None):
        return {"clase": clase, "senal": senal, "conflicto_retroactivo": conflicto}

    # ---- deteccion de RUIDO (titulo que no es denominacion) ----
    def es_ruido(self, denom):
        """RUIDO = titulo-con-Ref (prefijo de codigo NLP y NADA util despues) o
        titulo-localidad (solo un token que es localidad). Conservador: si tras
        limpiar el prefijo queda una denominacion real, NO es ruido (se clasifica
        normal). Devuelve motivo o None."""
        n = _norm(denom)
        # prefijo de codigo NLP sin denominacion util despues
        limpio = self.prefijo_ruido.sub("", n).strip()
        if self.prefijo_ruido.match(n) and (not limpio or self.head(denom) == ""):
            return "prefijo-codigo-NLP sin denominacion util"
        # head vacio tras limpieza (localidad/separador puro)
        if not self.head(denom):
            return "sin denominacion identificable (localidad/ruido)"
        return None
