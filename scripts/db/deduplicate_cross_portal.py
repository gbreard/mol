#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
deduplicate_cross_portal.py
===========================
Detecta y marca ofertas duplicadas entre portales (Bumeran, ZonaJobs, etc.)

Algoritmo:
1. BLOCKING: Agrupa por (provincia, semana) para reducir comparaciones
2. SCORING: Calcula similitud híbrida (título + descripción + empresa)
3. DECISIÓN: Marca duplicados con score >= umbral

Uso:
    python deduplicate_cross_portal.py [--threshold 0.85] [--dry-run]
"""

import sqlite3
import re
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
import hashlib

try:
    from rapidfuzz import fuzz
    from rapidfuzz.distance import Levenshtein
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    print("WARNING: rapidfuzz no disponible. Instalar con: pip install rapidfuzz")
    RAPIDFUZZ_AVAILABLE = False

try:
    from datasketch import MinHash, MinHashLSH
    MINHASH_AVAILABLE = True
except ImportError:
    print("WARNING: datasketch no disponible. Usando fallback para descripción.")
    MINHASH_AVAILABLE = False

# Configuración
DB_PATH = Path(__file__).parent / 'bumeran_scraping.db'

# Pesos del scoring
PESO_TITULO = 0.40
PESO_DESCRIPCION = 0.35
PESO_EMPRESA = 0.15
PESO_SALARIO = 0.10

# Umbrales
THRESHOLD_CONFIRMADO = 0.85
THRESHOLD_PROBABLE = 0.70

# Normalización de títulos
NORMALIZACIONES_TITULO = [
    (r'\bsr\.?\b', 'senior'),
    (r'\bjr\.?\b', 'junior'),
    (r'\bsemi\s*sr\.?\b', 'semi senior'),
    (r'\bssa\.?\b', 'senior'),
    (r'\bgerente\b', 'gerente'),
    (r'\s+', ' '),  # múltiples espacios
    (r'[^\w\s]', ''),  # puntuación
]

# Empresas a ignorar en matching
EMPRESAS_CONFIDENCIALES = {
    'confidencial', 'empresa confidencial', 'importante empresa',
    'empresa lider', 'empresa líder', 'consultora', 'consultora de rrhh',
    'empresa de primer nivel', 'multinacional', 'pyme', ''
}


def normalizar_titulo(titulo: str) -> str:
    """Normaliza título para comparación"""
    if not titulo:
        return ''
    texto = titulo.lower().strip()
    for patron, reemplazo in NORMALIZACIONES_TITULO:
        texto = re.sub(patron, reemplazo, texto)
    return texto.strip()


def normalizar_empresa(empresa: str) -> str:
    """Normaliza nombre de empresa"""
    if not empresa:
        return ''
    texto = empresa.lower().strip()
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()


def es_empresa_confidencial(empresa: str) -> bool:
    """Detecta si la empresa es genérica/confidencial"""
    if not empresa:
        return True
    return normalizar_empresa(empresa) in EMPRESAS_CONFIDENCIALES


def calcular_similitud_titulo(t1: str, t2: str) -> float:
    """Calcula similitud entre títulos usando RapidFuzz"""
    if not t1 or not t2:
        return 0.0

    t1_norm = normalizar_titulo(t1)
    t2_norm = normalizar_titulo(t2)

    if not t1_norm or not t2_norm:
        return 0.0

    if RAPIDFUZZ_AVAILABLE:
        # Combinar ratio y partial_ratio para robustez
        ratio = fuzz.ratio(t1_norm, t2_norm) / 100.0
        partial = fuzz.partial_ratio(t1_norm, t2_norm) / 100.0
        token_sort = fuzz.token_sort_ratio(t1_norm, t2_norm) / 100.0
        return max(ratio, partial * 0.9, token_sort * 0.95)
    else:
        # Fallback: Jaccard sobre tokens
        tokens1 = set(t1_norm.split())
        tokens2 = set(t2_norm.split())
        if not tokens1 or not tokens2:
            return 0.0
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        return intersection / union if union > 0 else 0.0


def calcular_minhash(texto: str, num_perm: int = 128) -> Optional['MinHash']:
    """Calcula MinHash de un texto para comparación eficiente"""
    if not MINHASH_AVAILABLE or not texto:
        return None

    # Tokenizar en shingles de 3 palabras
    palabras = texto.lower().split()
    if len(palabras) < 3:
        return None

    shingles = set()
    for i in range(len(palabras) - 2):
        shingle = ' '.join(palabras[i:i+3])
        shingles.add(shingle)

    if not shingles:
        return None

    m = MinHash(num_perm=num_perm)
    for shingle in shingles:
        m.update(shingle.encode('utf-8'))
    return m


def calcular_similitud_descripcion(d1: str, d2: str,
                                    minhash1: Optional['MinHash'] = None,
                                    minhash2: Optional['MinHash'] = None) -> float:
    """Calcula similitud entre descripciones"""
    if not d1 or not d2:
        return 0.0

    # Usar solo primeros 500 caracteres (robusto a truncamiento)
    d1_short = d1[:500].lower()
    d2_short = d2[:500].lower()

    # Si tenemos MinHash, usar Jaccard estimado
    if minhash1 and minhash2:
        return minhash1.jaccard(minhash2)

    # Fallback: similitud por tokens
    if RAPIDFUZZ_AVAILABLE:
        return fuzz.token_set_ratio(d1_short, d2_short) / 100.0
    else:
        tokens1 = set(d1_short.split())
        tokens2 = set(d2_short.split())
        if not tokens1 or not tokens2:
            return 0.0
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        return intersection / union if union > 0 else 0.0


def calcular_similitud_empresa(e1: str, e2: str) -> Tuple[float, bool]:
    """
    Calcula similitud entre empresas.
    Retorna (score, debe_ignorar) - debe_ignorar=True si alguna es confidencial
    """
    # Si alguna es confidencial, ignorar este campo
    if es_empresa_confidencial(e1) or es_empresa_confidencial(e2):
        return 0.0, True

    e1_norm = normalizar_empresa(e1)
    e2_norm = normalizar_empresa(e2)

    if not e1_norm or not e2_norm:
        return 0.0, True

    if RAPIDFUZZ_AVAILABLE:
        ratio = fuzz.ratio(e1_norm, e2_norm) / 100.0
        partial = fuzz.partial_ratio(e1_norm, e2_norm) / 100.0
        return max(ratio, partial * 0.9), False
    else:
        tokens1 = set(e1_norm.split())
        tokens2 = set(e2_norm.split())
        if not tokens1 or not tokens2:
            return 0.0, True
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        return intersection / union if union > 0 else 0.0, False


def calcular_similitud_salario(s1: Optional[float], s2: Optional[float]) -> float:
    """Calcula similitud de salarios (bonus si coinciden)"""
    if s1 is None or s2 is None:
        return 0.0  # Sin información, no penaliza ni bonifica

    if s1 == 0 or s2 == 0:
        return 0.0

    # Calcular diferencia porcentual
    diff_pct = abs(s1 - s2) / max(s1, s2)

    if diff_pct < 0.05:  # Menos de 5% de diferencia
        return 1.0
    elif diff_pct < 0.15:  # Menos de 15%
        return 0.7
    elif diff_pct < 0.30:  # Menos de 30%
        return 0.3
    else:
        return 0.0


def calcular_score_duplicado(oferta1: dict, oferta2: dict) -> Tuple[float, dict]:
    """
    Calcula score de duplicación entre dos ofertas.

    Returns:
        Tuple[float, dict]: (score_final, detalle_scores)
    """
    detalle = {}

    # Título (40%)
    sim_titulo = calcular_similitud_titulo(
        oferta1.get('titulo', ''),
        oferta2.get('titulo', '')
    )
    detalle['titulo'] = sim_titulo

    # Descripción (35%)
    sim_desc = calcular_similitud_descripcion(
        oferta1.get('descripcion', ''),
        oferta2.get('descripcion', ''),
        oferta1.get('_minhash'),
        oferta2.get('_minhash')
    )
    detalle['descripcion'] = sim_desc

    # Empresa (15%)
    sim_empresa, ignorar_empresa = calcular_similitud_empresa(
        oferta1.get('empresa', ''),
        oferta2.get('empresa', '')
    )
    detalle['empresa'] = sim_empresa
    detalle['empresa_ignorada'] = ignorar_empresa

    # Salario (10%)
    sim_salario = calcular_similitud_salario(
        oferta1.get('salario'),
        oferta2.get('salario')
    )
    detalle['salario'] = sim_salario

    # Calcular score final
    if ignorar_empresa:
        # Redistribuir peso de empresa entre título y descripción
        peso_titulo_adj = PESO_TITULO + PESO_EMPRESA * 0.6
        peso_desc_adj = PESO_DESCRIPCION + PESO_EMPRESA * 0.4
        score = (
            sim_titulo * peso_titulo_adj +
            sim_desc * peso_desc_adj +
            sim_salario * PESO_SALARIO
        )
    else:
        score = (
            sim_titulo * PESO_TITULO +
            sim_desc * PESO_DESCRIPCION +
            sim_empresa * PESO_EMPRESA +
            sim_salario * PESO_SALARIO
        )

    detalle['score_final'] = score
    return score, detalle


def obtener_semana(fecha_str: str) -> str:
    """Obtiene identificador de semana (año-semana) de una fecha"""
    if not fecha_str:
        return 'unknown'
    try:
        # Intentar varios formatos
        for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y']:
            try:
                fecha = datetime.strptime(fecha_str[:10], fmt[:len(fecha_str[:10])])
                # Extender a semana ± 1 para capturar ofertas en límites
                return fecha.strftime('%Y-%W')
            except:
                continue
        return 'unknown'
    except:
        return 'unknown'


def generar_blocking_key(oferta: dict) -> str:
    """Genera clave de blocking para una oferta"""
    provincia = (oferta.get('provincia', '') or 'unknown').lower().strip()
    semana = obtener_semana(oferta.get('fecha_publicacion', ''))
    return f"{provincia}|{semana}"


class CrossPortalDeduplicator:
    """Deduplicador de ofertas entre portales"""

    def __init__(self, db_path: Path = DB_PATH, threshold: float = THRESHOLD_CONFIRMADO):
        self.db_path = db_path
        self.threshold = threshold
        self.conn = None
        self.stats = {
            'ofertas_procesadas': 0,
            'comparaciones_realizadas': 0,
            'duplicados_confirmados': 0,
            'duplicados_probables': 0,
            'grupos_creados': 0
        }

    def conectar(self):
        """Conecta a la base de datos"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        print(f"[OK] Conectado a: {self.db_path}")

    def crear_tabla_duplicados(self):
        """Crea tabla para almacenar duplicados detectados"""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ofertas_duplicados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_oferta_1 TEXT NOT NULL,
                portal_1 TEXT,
                id_oferta_2 TEXT NOT NULL,
                portal_2 TEXT,
                score_similitud REAL,
                score_titulo REAL,
                score_descripcion REAL,
                score_empresa REAL,
                estado TEXT DEFAULT 'detectado',  -- detectado, confirmado, rechazado
                grupo_duplicado TEXT,  -- ID del grupo de duplicados
                detectado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(id_oferta_1, id_oferta_2)
            )
        """)

        # Agregar columna de grupo a ofertas si no existe
        cursor.execute("PRAGMA table_info(ofertas)")
        columnas = [row[1] for row in cursor.fetchall()]

        if 'grupo_duplicado' not in columnas:
            cursor.execute("ALTER TABLE ofertas ADD COLUMN grupo_duplicado TEXT")
            print("  [+] Columna grupo_duplicado agregada a ofertas")

        if 'es_duplicado' not in columnas:
            cursor.execute("ALTER TABLE ofertas ADD COLUMN es_duplicado INTEGER DEFAULT 0")
            print("  [+] Columna es_duplicado agregada a ofertas")

        if 'es_canonico' not in columnas:
            cursor.execute("ALTER TABLE ofertas ADD COLUMN es_canonico INTEGER DEFAULT 1")
            print("  [+] Columna es_canonico agregada a ofertas")

        self.conn.commit()
        print("[OK] Tabla ofertas_duplicados creada/verificada")

    def obtener_ofertas(self) -> List[dict]:
        """Obtiene todas las ofertas para deduplicación"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                id_oferta,
                titulo,
                descripcion_utf8 as descripcion,
                empresa,
                provincia_normalizada as provincia,
                localidad_normalizada as localidad,
                fecha_publicacion,
                salario_minimo,
                salario_maximo,
                portal,
                url_oferta
            FROM ofertas
            WHERE titulo IS NOT NULL
            ORDER BY fecha_publicacion DESC, id_oferta
        """)

        ofertas = []
        for row in cursor.fetchall():
            oferta = dict(row)
            # Calcular salario promedio si existe
            sal_min = oferta.get('salario_minimo')
            sal_max = oferta.get('salario_maximo')
            if sal_min and sal_max:
                oferta['salario'] = (sal_min + sal_max) / 2
            elif sal_min:
                oferta['salario'] = sal_min
            elif sal_max:
                oferta['salario'] = sal_max
            else:
                oferta['salario'] = None

            # Pre-calcular MinHash de descripción
            if MINHASH_AVAILABLE and oferta.get('descripcion'):
                oferta['_minhash'] = calcular_minhash(oferta['descripcion'][:500])

            ofertas.append(oferta)

        return ofertas

    def crear_bloques(self, ofertas: List[dict]) -> Dict[str, List[dict]]:
        """Agrupa ofertas por blocking key"""
        bloques = defaultdict(list)

        for oferta in ofertas:
            key = generar_blocking_key(oferta)
            bloques[key].append(oferta)

        # Estadísticas de blocking
        n_bloques = len(bloques)
        avg_size = sum(len(b) for b in bloques.values()) / max(1, n_bloques)
        max_size = max(len(b) for b in bloques.values()) if bloques else 0

        print(f"  Bloques creados: {n_bloques}")
        print(f"  Tamaño promedio: {avg_size:.1f} ofertas/bloque")
        print(f"  Bloque más grande: {max_size} ofertas")

        return bloques

    def encontrar_duplicados(self, ofertas: List[dict], dry_run: bool = False) -> List[dict]:
        """
        Encuentra duplicados entre ofertas usando blocking + scoring.

        Returns:
            Lista de pares duplicados con scores
        """
        print("\n[1] CREANDO BLOQUES...")
        bloques = self.crear_bloques(ofertas)

        print("\n[2] COMPARANDO DENTRO DE BLOQUES...")
        duplicados = []

        for key, bloque in bloques.items():
            n = len(bloque)
            if n < 2:
                continue

            # Comparar todos los pares dentro del bloque
            for i in range(n):
                for j in range(i + 1, n):
                    o1 = bloque[i]
                    o2 = bloque[j]

                    # Skip si son del mismo portal (ya deduplicados internamente)
                    if o1.get('portal') == o2.get('portal'):
                        continue

                    self.stats['comparaciones_realizadas'] += 1

                    score, detalle = calcular_score_duplicado(o1, o2)

                    if score >= THRESHOLD_PROBABLE:
                        duplicado = {
                            'id_oferta_1': o1['id_oferta'],
                            'portal_1': o1.get('portal', 'unknown'),
                            'titulo_1': o1.get('titulo', '')[:60],
                            'id_oferta_2': o2['id_oferta'],
                            'portal_2': o2.get('portal', 'unknown'),
                            'titulo_2': o2.get('titulo', '')[:60],
                            'score': score,
                            'detalle': detalle,
                            'confirmado': score >= self.threshold
                        }
                        duplicados.append(duplicado)

                        if score >= self.threshold:
                            self.stats['duplicados_confirmados'] += 1
                        else:
                            self.stats['duplicados_probables'] += 1

        return duplicados

    def asignar_grupos(self, duplicados: List[dict]) -> Dict[str, str]:
        """
        Asigna grupos de duplicados usando Union-Find.

        Returns:
            Dict mapping id_oferta -> grupo_id
        """
        # Union-Find
        parent = {}

        def find(x):
            if x not in parent:
                parent[x] = x
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Unir duplicados confirmados
        for dup in duplicados:
            if dup['confirmado']:
                union(dup['id_oferta_1'], dup['id_oferta_2'])

        # Generar grupo IDs
        grupos = {}
        grupo_counter = 0

        for id_oferta in parent:
            root = find(id_oferta)
            if root not in grupos:
                grupo_counter += 1
                grupos[root] = f"DUP-{grupo_counter:05d}"

        # Mapear cada oferta a su grupo
        resultado = {}
        for id_oferta in parent:
            root = find(id_oferta)
            resultado[id_oferta] = grupos[root]

        self.stats['grupos_creados'] = grupo_counter
        return resultado

    def guardar_resultados(self, duplicados: List[dict], grupos: Dict[str, str],
                           dry_run: bool = False):
        """Guarda resultados en la base de datos"""
        if dry_run:
            print("\n[DRY-RUN] No se guardan cambios")
            return

        cursor = self.conn.cursor()

        # Guardar pares de duplicados
        for dup in duplicados:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO ofertas_duplicados
                    (id_oferta_1, portal_1, id_oferta_2, portal_2,
                     score_similitud, score_titulo, score_descripcion, score_empresa,
                     estado, grupo_duplicado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(dup['id_oferta_1']),
                    dup['portal_1'],
                    str(dup['id_oferta_2']),
                    dup['portal_2'],
                    dup['score'],
                    dup['detalle']['titulo'],
                    dup['detalle']['descripcion'],
                    dup['detalle']['empresa'],
                    'confirmado' if dup['confirmado'] else 'probable',
                    grupos.get(dup['id_oferta_1'], grupos.get(dup['id_oferta_2']))
                ))
            except Exception as e:
                print(f"  Error guardando duplicado: {e}")

        # Actualizar ofertas con grupo
        for id_oferta, grupo in grupos.items():
            cursor.execute("""
                UPDATE ofertas
                SET grupo_duplicado = ?, es_duplicado = 1
                WHERE id_oferta = ? OR CAST(id_oferta AS TEXT) = ?
            """, (grupo, id_oferta, str(id_oferta)))

        # Marcar canónicos (el primero de cada grupo por fecha)
        cursor.execute("""
            UPDATE ofertas SET es_canonico = 0 WHERE es_duplicado = 1
        """)

        cursor.execute("""
            WITH canonicos AS (
                SELECT id_oferta, grupo_duplicado,
                       ROW_NUMBER() OVER (
                           PARTITION BY grupo_duplicado
                           ORDER BY fecha_publicacion ASC, id_oferta ASC
                       ) as rn
                FROM ofertas
                WHERE grupo_duplicado IS NOT NULL
            )
            UPDATE ofertas
            SET es_canonico = 1
            WHERE id_oferta IN (SELECT id_oferta FROM canonicos WHERE rn = 1)
        """)

        self.conn.commit()
        print(f"\n[OK] Resultados guardados")

    def ejecutar(self, dry_run: bool = False):
        """Ejecuta el proceso completo de deduplicación"""
        print("=" * 70)
        print("DEDUPLICACIÓN CROSS-PORTAL")
        print(f"Threshold: {self.threshold}")
        print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        self.conectar()
        self.crear_tabla_duplicados()

        # Obtener ofertas
        print("\n[0] CARGANDO OFERTAS...")
        ofertas = self.obtener_ofertas()
        self.stats['ofertas_procesadas'] = len(ofertas)
        print(f"  Total ofertas: {len(ofertas):,}")

        # Contar por portal
        portales = defaultdict(int)
        for o in ofertas:
            portales[o.get('portal', 'unknown')] += 1
        print("  Por portal:")
        for portal, count in sorted(portales.items()):
            print(f"    {portal}: {count:,}")

        # Encontrar duplicados
        duplicados = self.encontrar_duplicados(ofertas, dry_run)

        # Asignar grupos
        print("\n[3] ASIGNANDO GRUPOS...")
        grupos = self.asignar_grupos(duplicados)

        # Guardar
        print("\n[4] GUARDANDO RESULTADOS...")
        self.guardar_resultados(duplicados, grupos, dry_run)

        # Reporte
        print("\n" + "=" * 70)
        print("RESUMEN")
        print("=" * 70)
        print(f"  Ofertas procesadas:      {self.stats['ofertas_procesadas']:,}")
        print(f"  Comparaciones:           {self.stats['comparaciones_realizadas']:,}")
        print(f"  Duplicados confirmados:  {self.stats['duplicados_confirmados']:,}")
        print(f"  Duplicados probables:    {self.stats['duplicados_probables']:,}")
        print(f"  Grupos creados:          {self.stats['grupos_creados']:,}")

        if duplicados:
            print("\n  Top 10 duplicados por score:")
            for dup in sorted(duplicados, key=lambda x: -x['score'])[:10]:
                print(f"    [{dup['score']:.2f}] {dup['portal_1']}:{dup['id_oferta_1'][:8]} <-> {dup['portal_2']}:{dup['id_oferta_2'][:8]}")
                print(f"           {dup['titulo_1'][:40]}")

        print("=" * 70)

        return duplicados


def main():
    parser = argparse.ArgumentParser(description='Deduplicación cross-portal de ofertas')
    parser.add_argument('--threshold', type=float, default=THRESHOLD_CONFIRMADO,
                        help=f'Umbral de similitud para confirmar duplicado (default: {THRESHOLD_CONFIRMADO})')
    parser.add_argument('--dry-run', action='store_true',
                        help='Ejecutar sin guardar cambios')
    args = parser.parse_args()

    deduplicator = CrossPortalDeduplicator(threshold=args.threshold)
    deduplicator.ejecutar(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
