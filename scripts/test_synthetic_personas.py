#!/usr/bin/env python3
"""
Test de personas sintéticas para S2 Oficina de Empleo.

Crea 8 personas con datos inventados, les asigna skills REALES de ESCO
por las 4 vías de captura (ocupación, tarea, texto, formación),
y testea el matching contra ofertas reales en Supabase.

Uso:
    python scripts/test_synthetic_personas.py                # Crear + testear
    python scripts/test_synthetic_personas.py --test-only    # Solo testear (ya creadas)
    python scripts/test_synthetic_personas.py --cleanup      # Borrar personas sintéticas
    python scripts/test_synthetic_personas.py --dry-run      # Ver qué haría sin tocar Supabase
"""

import json
import sys
import os
import argparse
from datetime import datetime
from collections import defaultdict

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Worktree puede no tener todos los archivos de datos; fallback al repo principal
MAIN_REPO = "/mnt/d/OEDE/Webscrapping"


def _resolve(path):
    """Busca en BASE_DIR primero, fallback a MAIN_REPO."""
    full = os.path.join(BASE_DIR, path)
    if os.path.exists(full):
        return full
    alt = os.path.join(MAIN_REPO, path)
    if os.path.exists(alt):
        return alt
    return full  # devolver el original para que el error sea claro


SUPABASE_CONFIG = _resolve("config/supabase_config.json")
ESCO_OCC_SKILLS = _resolve("database/embeddings/esco_occupation_skills.json")
ESCO_OCC_META = _resolve("database/embeddings/esco_occupations_metadata.json")
SKILLS_SEARCHABLE = _resolve("fase3_dashboard/mol-dashboard/public/data/skills_searchable.json")

# DNI prefix para identificar sintéticos (fácil de limpiar)
SYNTHETIC_DNI_PREFIX = "SYNTH-"

# ---------------------------------------------------------------------------
# Datos de las 8 personas sintéticas
# ---------------------------------------------------------------------------

PERSONAS = [
    # --- Vía 1: OCUPACIÓN (skills vienen de la ocupación ESCO) ---
    {
        "nombre": "Juan Pérez",
        "dni": f"{SYNTHETIC_DNI_PREFIX}001",
        "edad": 32,
        "nivel_educativo": "Secundario",
        "ubicacion": "La Matanza, Buenos Aires",
        "telefono": "11-5555-0001",
        "email": "juan.perez@test.synth",
        "origen": "S2",
        "via_principal": "ocupacion",
        "isco_target": "5223",
        "ocupacion_label": "Vendedor especializado",
        "descripcion_test": "Vendedor con secundario, zona GBA. Skills de ocupación ESCO.",
    },
    {
        "nombre": "María López",
        "dni": f"{SYNTHETIC_DNI_PREFIX}002",
        "edad": 28,
        "nivel_educativo": "Universitario",
        "ubicacion": "Córdoba Capital, Córdoba",
        "telefono": "351-555-0002",
        "email": "maria.lopez@test.synth",
        "origen": "S2",
        "via_principal": "ocupacion",
        "isco_target": "2411",
        "ocupacion_label": "Contadora",
        "descripcion_test": "Contadora universitaria, Córdoba. Skills de ocupación ESCO.",
    },

    # --- Vía 2: TAREA/SKILL (skills buscadas por keyword) ---
    {
        "nombre": "Carlos Gómez",
        "dni": f"{SYNTHETIC_DNI_PREFIX}003",
        "edad": 26,
        "nivel_educativo": "Universitario",
        "ubicacion": "CABA",
        "telefono": "11-5555-0003",
        "email": "carlos.gomez@test.synth",
        "origen": "S1",
        "via_principal": "tarea",
        "keywords_skills": ["programación", "python", "base de datos", "software", "analizar datos"],
        "isco_target": "2512",
        "ocupacion_label": "Desarrollador de software",
        "descripcion_test": "Dev junior, CABA. Skills buscadas por keyword (vía tarea).",
    },
    {
        "nombre": "Patricia Ruiz",
        "dni": f"{SYNTHETIC_DNI_PREFIX}006",
        "edad": 35,
        "nivel_educativo": "Secundario",
        "ubicacion": "Rosario, Santa Fe",
        "telefono": "341-555-0006",
        "email": "patricia.ruiz@test.synth",
        "origen": "S2",
        "via_principal": "tarea",
        "keywords_skills": ["atención", "cliente", "servicio", "alimentos", "higiene"],
        "isco_target": "5131",
        "ocupacion_label": "Camarera",
        "descripcion_test": "Camarera en Rosario. Skills buscadas por keyword (vía tarea).",
    },

    # --- Vía 3: TEXTO LIBRE (skills extraídas de descripción narrativa) ---
    {
        "nombre": "Luis Fernández",
        "dni": f"{SYNTHETIC_DNI_PREFIX}005",
        "edad": 45,
        "nivel_educativo": "Primario",
        "ubicacion": "Quilmes, Buenos Aires",
        "telefono": "11-5555-0005",
        "email": "luis.fernandez@test.synth",
        "origen": "S2",
        "via_principal": "texto",
        "texto_libre": (
            "Trabajo hace 8 años manejando camiones de reparto en zona sur del GBA. "
            "Hago entregas de mercadería, manejo camiones de hasta 5 toneladas, "
            "tengo registro profesional, organizo las rutas de entrega y controlo "
            "la carga y descarga. También llevo el control del combustible y "
            "mantenimiento básico del vehículo."
        ),
        "isco_target": "8322",
        "ocupacion_label": "Conductor de reparto",
        "descripcion_test": "Conductor 45 años, primario. Skills de texto libre narrativo.",
    },
    {
        "nombre": "Lucía Torres",
        "dni": f"{SYNTHETIC_DNI_PREFIX}008",
        "edad": 30,
        "nivel_educativo": "Universitario",
        "ubicacion": "CABA",
        "telefono": "11-5555-0008",
        "email": "lucia.torres@test.synth",
        "origen": "S1",
        "via_principal": "texto",
        "texto_libre": (
            "Soy abogada con 5 años de experiencia en derecho laboral. "
            "Redacto contratos, hago mediaciones, asesoro empresas en temas "
            "de despidos y convenios colectivos. Manejo expedientes judiciales, "
            "presento escritos y llevo audiencias. También tengo experiencia "
            "en compliance y normativa de protección de datos."
        ),
        "isco_target": "2611",
        "ocupacion_label": "Abogada",
        "descripcion_test": "Abogada laboralista, CABA. Skills de texto libre narrativo.",
    },

    # --- Vía 4: FORMACIÓN (skills asociadas a título/certificación) ---
    {
        "nombre": "Ana Martínez",
        "dni": f"{SYNTHETIC_DNI_PREFIX}004",
        "edad": 22,
        "nivel_educativo": "Terciario",
        "ubicacion": "Mendoza Capital, Mendoza",
        "telefono": "261-555-0004",
        "email": "ana.martinez@test.synth",
        "origen": "S1",
        "via_principal": "formacion",
        "formacion_keywords": ["administración", "contabilidad", "organizar", "oficina", "archivo"],
        "formacion_titulo": "Tecnicatura en Administración de Empresas",
        "isco_target": "4110",
        "ocupacion_label": "Empleada de oficina",
        "descripcion_test": "Administrativa junior, Mendoza. Skills de formación terciaria.",
    },
    {
        "nombre": "Diego Morales",
        "dni": f"{SYNTHETIC_DNI_PREFIX}007",
        "edad": 40,
        "nivel_educativo": "Secundario",
        "ubicacion": "Tucumán Capital, Tucumán",
        "telefono": "381-555-0007",
        "email": "diego.morales@test.synth",
        "origen": "S2",
        "via_principal": "formacion",
        "formacion_keywords": ["logística", "almacén", "inventario", "carga", "depósito"],
        "formacion_titulo": "Curso de Operador de Depósito y Logística",
        "isco_target": "9333",
        "ocupacion_label": "Mozo de almacén",
        "descripcion_test": "Operario logístico, Tucumán. Skills de curso de formación.",
    },
]


# ---------------------------------------------------------------------------
# Carga de datos ESCO
# ---------------------------------------------------------------------------

def load_esco_data():
    """Carga los 3 archivos ESCO necesarios."""
    with open(ESCO_OCC_SKILLS) as f:
        occ_skills_raw = json.load(f)
    occ_skills = occ_skills_raw.get("occupation_skills", occ_skills_raw)

    with open(ESCO_OCC_META) as f:
        occ_meta = json.load(f)

    with open(SKILLS_SEARCHABLE) as f:
        skills_raw = json.load(f)
    all_skills = skills_raw.get("skills", skills_raw)

    return occ_skills, occ_meta, all_skills


def find_occupation_uri(occ_meta, isco_code):
    """Encuentra la URI de una ocupación por ISCO code."""
    for m in occ_meta:
        code = m.get("isco_code", "").replace("C", "")
        if code == isco_code:
            return m["uri"], m["label"]
    return None, None


def get_skills_via_ocupacion(occ_skills, occ_meta, isco_code, max_skills=15):
    """Vía 1: Skills de la ocupación ESCO (essential + optional)."""
    uri, label = find_occupation_uri(occ_meta, isco_code)
    if not uri or uri not in occ_skills:
        return []

    skills_data = occ_skills[uri]
    result = []

    for s in skills_data.get("essential", [])[:max_skills]:
        result.append({
            "skill_uri": s["skill_uri"],
            "skill_label": s["skill_label"],
            "via_captura": "ocupacion",
            "estado": "confirmada",
            "confianza": 0.9,
        })

    remaining = max_skills - len(result)
    for s in skills_data.get("optional", [])[:remaining]:
        result.append({
            "skill_uri": s["skill_uri"],
            "skill_label": s["skill_label"],
            "via_captura": "ocupacion",
            "estado": "sugerida",
            "confianza": 0.6,
        })

    return result


def get_skills_via_tarea(all_skills, keywords, max_per_keyword=3, max_total=15):
    """Vía 2: Skills buscadas por keyword (simula búsqueda del usuario)."""
    result = []
    seen_uris = set()

    for kw in keywords:
        kw_lower = kw.lower()
        matches = [
            s for s in all_skills
            if kw_lower in s.get("label", "").lower()
            and s.get("id") not in seen_uris
        ]
        # Priorizar por frecuencia (más usadas en ofertas)
        matches.sort(key=lambda s: s.get("total", 0), reverse=True)

        for s in matches[:max_per_keyword]:
            if len(result) >= max_total:
                break
            uri = f"http://data.europa.eu/esco/skill/{s['id']}" if not s["id"].startswith("http") else s["id"]
            result.append({
                "skill_uri": uri,
                "skill_label": s["label"],
                "via_captura": "tarea",
                "estado": "confirmada",
                "confianza": 0.85,
            })
            seen_uris.add(s["id"])

    return result


def get_skills_via_texto(all_skills, texto, max_skills=12):
    """Vía 3: Skills extraídas de texto libre (simulación con keyword matching).

    En producción esto lo haría el NLP (/api/skills-extract-from-text).
    Aquí simulamos buscando keywords del texto en el catálogo de skills.
    """
    palabras = set(texto.lower().replace(",", "").replace(".", "").split())
    # Filtrar stopwords cortas
    palabras = {p for p in palabras if len(p) > 4}

    scored = []
    for s in all_skills:
        label = s.get("label", "").lower()
        label_words = set(label.split())
        overlap = len(palabras & label_words)
        if overlap > 0:
            scored.append((overlap, s.get("total", 0), s))

    # Ordenar por overlap desc, luego por frecuencia
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)

    result = []
    seen = set()
    for _, _, s in scored[:max_skills * 2]:
        if len(result) >= max_skills:
            break
        uri = f"http://data.europa.eu/esco/skill/{s['id']}" if not s["id"].startswith("http") else s["id"]
        if uri in seen:
            continue
        seen.add(uri)
        result.append({
            "skill_uri": uri,
            "skill_label": s["label"],
            "via_captura": "texto",
            "estado": "sugerida",
            "confianza": 0.7,
        })

    return result


def get_skills_via_formacion(all_skills, keywords, max_skills=12):
    """Vía 4: Skills asociadas a formación (simula mapeo título→skills).

    En producción esto usaría /api/training-suggestions.
    Aquí simulamos buscando keywords de la formación en el catálogo.
    """
    return [
        {**s, "via_captura": "formacion", "confianza": 0.75}
        for s in get_skills_via_tarea(all_skills, keywords, max_per_keyword=3, max_total=max_skills)
    ]


# ---------------------------------------------------------------------------
# Supabase operations
# ---------------------------------------------------------------------------

def get_supabase_client():
    config = json.load(open(SUPABASE_CONFIG))
    from supabase import create_client
    return create_client(config["url"], config["service_role_key"])


def cleanup_synthetic(client):
    """Elimina todas las personas sintéticas y sus datos relacionados."""
    # Buscar personas sintéticas
    result = client.table("personas").select("id").like("dni", f"{SYNTHETIC_DNI_PREFIX}%").execute()
    if not result.data:
        print("No hay personas sintéticas para limpiar.")
        return 0

    persona_ids = [r["id"] for r in result.data]
    print(f"Encontradas {len(persona_ids)} personas sintéticas.")

    # Buscar perfiles
    perfiles = client.table("perfiles").select("id").in_("persona_id", persona_ids).execute()
    perfil_ids = [p["id"] for p in perfiles.data] if perfiles.data else []

    # Borrar en orden (por FK constraints)
    if perfil_ids:
        client.table("perfil_skills").delete().in_("perfil_id", perfil_ids).execute()
        print(f"  Borradas skills de {len(perfil_ids)} perfiles")
        client.table("perfiles").delete().in_("id", perfil_ids).execute()
        print(f"  Borrados {len(perfil_ids)} perfiles")

    # Borrar casos y derivaciones
    casos = client.table("casos").select("id").in_("persona_id", persona_ids).execute()
    if casos.data:
        caso_ids = [c["id"] for c in casos.data]
        client.table("derivaciones").delete().in_("caso_id", caso_ids).execute()
        client.table("eventos_caso").delete().in_("entidad_id", caso_ids).execute()
        client.table("casos").delete().in_("id", caso_ids).execute()
        print(f"  Borrados {len(caso_ids)} casos")

    # Borrar personas
    client.table("personas").delete().in_("id", persona_ids).execute()
    print(f"  Borradas {len(persona_ids)} personas")

    return len(persona_ids)


def create_personas_and_skills(client, occ_skills, occ_meta, all_skills, dry_run=False):
    """Crea las 8 personas sintéticas con sus skills."""
    created = []

    for p in PERSONAS:
        via = p["via_principal"]
        print(f"\n{'='*60}")
        print(f"  {p['nombre']} — Vía: {via} — {p['ocupacion_label']}")
        print(f"  {p['descripcion_test']}")
        print(f"{'='*60}")

        # Obtener skills según la vía
        if via == "ocupacion":
            skills = get_skills_via_ocupacion(occ_skills, occ_meta, p["isco_target"])
        elif via == "tarea":
            skills = get_skills_via_tarea(all_skills, p["keywords_skills"])
        elif via == "texto":
            skills = get_skills_via_texto(all_skills, p["texto_libre"])
        elif via == "formacion":
            skills = get_skills_via_formacion(all_skills, p["formacion_keywords"])
        else:
            skills = []

        print(f"  Skills encontradas: {len(skills)}")
        for s in skills:
            est = "OK" if s["estado"] == "confirmada" else "?"
            print(f"    [{est}] {s['skill_label'][:50]:<50s} (conf: {s['confianza']:.1f}, vía: {s['via_captura']})")

        if dry_run:
            created.append({"persona": p, "skills": skills, "persona_id": "DRY-RUN", "perfil_id": "DRY-RUN"})
            continue

        # 1. Insertar persona
        persona_data = {
            "nombre": p["nombre"],
            "dni": p["dni"],
            "edad": p["edad"],
            "nivel_educativo": p["nivel_educativo"],
            "ubicacion": p["ubicacion"],
            "telefono": p["telefono"],
            "email": p["email"],
            "origen": p["origen"],
        }
        res = client.table("personas").insert(persona_data).execute()
        persona_id = res.data[0]["id"]

        # 2. Insertar perfil
        perfil_data = {
            "persona_id": persona_id,
            "origen": p["origen"],
            "completitud": len([s for s in skills if s["estado"] == "confirmada"]),
            "nivel_confianza": sum(s["confianza"] for s in skills) / len(skills) if skills else 0,
        }
        res = client.table("perfiles").insert(perfil_data).execute()
        perfil_id = res.data[0]["id"]

        # 3. Insertar skills
        if skills:
            skills_data = [
                {
                    "perfil_id": perfil_id,
                    "skill_uri": s["skill_uri"],
                    "skill_label": s["skill_label"],
                    "via_captura": s["via_captura"],
                    "estado": s["estado"],
                    "confianza": s["confianza"],
                }
                for s in skills
            ]
            client.table("perfil_skills").insert(skills_data).execute()

        # 4. Crear caso en la OE
        caso_data = {
            "persona_id": persona_id,
            "estado": "perfil_completo" if len(skills) >= 3 else "en_diagnostico",
            "objetivo": "empleo",
            "prioridad": "normal",
            "nota_tecnico": f"Persona sintética de prueba. Vía captura: {via}. {p['descripcion_test']}",
        }
        res_caso = client.table("casos").insert(caso_data).execute()

        created.append({
            "persona": p,
            "skills": skills,
            "persona_id": persona_id,
            "perfil_id": perfil_id,
            "caso_id": res_caso.data[0]["id"],
        })
        print(f"  -> Persona: {persona_id[:8]}... | Perfil: {perfil_id[:8]}... | Skills: {len(skills)}")

    return created


# ---------------------------------------------------------------------------
# Test de matching
# ---------------------------------------------------------------------------

def test_matching(client, created_personas):
    """Testea matching de cada persona contra ofertas reales en Supabase."""
    print("\n")
    print("=" * 70)
    print("  TEST DE MATCHING — Personas sintéticas vs Ofertas reales")
    print("=" * 70)

    results = []

    for cp in created_personas:
        p = cp["persona"]
        skills = cp["skills"]
        isco = p["isco_target"]
        skill_uris = {s["skill_uri"] for s in skills}

        print(f"\n{'─'*60}")
        print(f"  {p['nombre']} | {p['ocupacion_label']} (ISCO {isco}) | Vía: {p['via_principal']}")
        print(f"  Skills: {len(skills)} | Ubicación: {p['ubicacion']}")
        print(f"{'─'*60}")

        # 1. Contar ofertas por ISCO
        ofertas_isco = client.table("ofertas_dashboard") \
            .select("id_oferta", count="exact") \
            .eq("isco_code", isco) \
            .limit(0).execute()
        total_ofertas = ofertas_isco.count or 0

        # 2. Obtener muestra de ofertas para calcular matching
        ofertas_sample = client.table("ofertas_dashboard") \
            .select("id_oferta,titulo,empresa,provincia") \
            .eq("isco_code", isco) \
            .limit(50).execute()

        if not ofertas_sample.data:
            print(f"  No hay ofertas con ISCO {isco}")
            results.append({
                "persona": p["nombre"],
                "via": p["via_principal"],
                "isco": isco,
                "total_ofertas": 0,
                "avg_match": 0,
                "best_match": 0,
                "skills_count": len(skills),
                "ofertas_con_skills": 0,
            })
            continue

        # 3. Para cada oferta, calcular match por skills
        oferta_ids = [str(o["id_oferta"]) for o in ofertas_sample.data]

        # Obtener skills de estas ofertas
        ofertas_skills = client.table("ofertas_skills") \
            .select("id_oferta,skill_uri,preferred_label") \
            .in_("id_oferta", oferta_ids) \
            .execute()

        # Agrupar skills por oferta
        skills_por_oferta = defaultdict(set)
        labels_por_oferta = defaultdict(dict)
        for os_row in (ofertas_skills.data or []):
            oid = str(os_row["id_oferta"])
            skills_por_oferta[oid].add(os_row["skill_uri"])
            labels_por_oferta[oid][os_row["skill_uri"]] = os_row["preferred_label"]

        # 4. Calcular match scores
        matches = []
        for o in ofertas_sample.data:
            oid = str(o["id_oferta"])
            oferta_skill_uris = skills_por_oferta.get(oid, set())
            if not oferta_skill_uris:
                continue

            cubiertas = skill_uris & oferta_skill_uris
            gap = oferta_skill_uris - skill_uris
            score = (len(cubiertas) / len(oferta_skill_uris)) * 100 if oferta_skill_uris else 0

            matches.append({
                "id_oferta": oid,
                "titulo": o["titulo"],
                "empresa": o.get("empresa", "?"),
                "provincia": o.get("provincia", "?"),
                "score": score,
                "cubiertas": len(cubiertas),
                "total_skills_oferta": len(oferta_skill_uris),
                "gap": len(gap),
                "skills_cubiertas": [labels_por_oferta[oid].get(u, u) for u in cubiertas],
                "skills_gap": [labels_por_oferta[oid].get(u, u) for u in list(gap)[:5]],
            })

        matches.sort(key=lambda m: m["score"], reverse=True)

        # 5. Estadísticas
        ofertas_con_skills = len([m for m in matches if m["total_skills_oferta"] > 0])
        scores = [m["score"] for m in matches if m["total_skills_oferta"] > 0]
        avg_match = sum(scores) / len(scores) if scores else 0
        best_match = max(scores) if scores else 0
        above_50 = len([s for s in scores if s >= 50])
        above_30 = len([s for s in scores if s >= 30])

        print(f"\n  RESULTADOS:")
        print(f"  Ofertas ISCO {isco} totales: {total_ofertas}")
        print(f"  Muestra analizada: {len(ofertas_sample.data)} ofertas")
        print(f"  Ofertas con skills: {ofertas_con_skills}")
        print(f"  Match promedio: {avg_match:.1f}%")
        print(f"  Mejor match: {best_match:.1f}%")
        print(f"  Ofertas con match >= 50%: {above_50}")
        print(f"  Ofertas con match >= 30%: {above_30}")

        # Top 3 mejores matches
        if matches:
            print(f"\n  TOP 3 MEJORES MATCHES:")
            for i, m in enumerate(matches[:3]):
                print(f"    {i+1}. [{m['score']:.0f}%] {m['titulo'][:45]} — {m['empresa'][:20]}")
                print(f"       Skills cubiertas ({m['cubiertas']}/{m['total_skills_oferta']}): "
                      f"{', '.join(m['skills_cubiertas'][:3])}")
                if m["skills_gap"]:
                    print(f"       Gap: {', '.join(m['skills_gap'][:3])}")

        # Skill gap más frecuente (qué le falta a esta persona)
        if matches:
            gap_counter = defaultdict(int)
            for m in matches:
                for sg in m["skills_gap"]:
                    gap_counter[sg] += 1
            top_gaps = sorted(gap_counter.items(), key=lambda x: x[1], reverse=True)[:5]
            if top_gaps:
                print(f"\n  SKILLS QUE MÁS LE FALTAN (gap frecuente):")
                for skill_label, count in top_gaps:
                    pct = (count / ofertas_con_skills * 100) if ofertas_con_skills else 0
                    print(f"    - {skill_label[:50]} (falta en {pct:.0f}% de las ofertas)")

        results.append({
            "persona": p["nombre"],
            "via": p["via_principal"],
            "isco": isco,
            "ocupacion": p["ocupacion_label"],
            "total_ofertas": total_ofertas,
            "muestra": len(ofertas_sample.data),
            "ofertas_con_skills": ofertas_con_skills,
            "avg_match": avg_match,
            "best_match": best_match,
            "above_50": above_50,
            "above_30": above_30,
            "skills_count": len(skills),
        })

    return results


def print_comparative_report(results):
    """Imprime reporte comparativo entre las 4 vías."""
    print("\n")
    print("=" * 70)
    print("  REPORTE COMPARATIVO POR VÍA DE CAPTURA")
    print("=" * 70)

    # Tabla resumen
    print(f"\n  {'Persona':<20s} {'Vía':<12s} {'Skills':<7s} {'Ofertas':<8s} "
          f"{'Avg%':<7s} {'Best%':<7s} {'>=50%':<6s} {'>=30%':<6s}")
    print(f"  {'─'*20} {'─'*12} {'─'*7} {'─'*8} {'─'*7} {'─'*7} {'─'*6} {'─'*6}")

    for r in results:
        print(f"  {r['persona']:<20s} {r['via']:<12s} {r['skills_count']:<7d} {r['total_ofertas']:<8d} "
              f"{r['avg_match']:<7.1f} {r['best_match']:<7.1f} {r['above_50']:<6d} {r['above_30']:<6d}")

    # Promedio por vía
    print(f"\n  PROMEDIO POR VÍA DE CAPTURA:")
    print(f"  {'─'*50}")
    vias = defaultdict(list)
    for r in results:
        vias[r["via"]].append(r)

    for via, items in sorted(vias.items()):
        avg_avg = sum(i["avg_match"] for i in items) / len(items)
        avg_best = sum(i["best_match"] for i in items) / len(items)
        avg_skills = sum(i["skills_count"] for i in items) / len(items)
        total_50 = sum(i["above_50"] for i in items)
        total_30 = sum(i["above_30"] for i in items)
        print(f"  {via:<12s} | Skills prom: {avg_skills:.0f} | Match prom: {avg_avg:.1f}% | "
              f"Best prom: {avg_best:.1f}% | >=50%: {total_50} | >=30%: {total_30}")

    # Conclusiones
    print(f"\n  CONCLUSIONES:")
    print(f"  {'─'*50}")

    best_via = max(vias.items(), key=lambda x: sum(i["avg_match"] for i in x[1]) / len(x[1]))
    worst_via = min(vias.items(), key=lambda x: sum(i["avg_match"] for i in x[1]) / len(x[1]))

    print(f"  Mejor vía de captura: {best_via[0]} "
          f"(avg match {sum(i['avg_match'] for i in best_via[1])/len(best_via[1]):.1f}%)")
    print(f"  Peor vía de captura:  {worst_via[0]} "
          f"(avg match {sum(i['avg_match'] for i in worst_via[1])/len(worst_via[1]):.1f}%)")

    no_match = [r for r in results if r["avg_match"] == 0]
    if no_match:
        print(f"\n  ATENCIÓN: {len(no_match)} persona(s) sin match:")
        for r in no_match:
            print(f"    - {r['persona']} ({r['via']}) — {r['total_ofertas']} ofertas ISCO pero 0 match")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Test personas sintéticas S2")
    parser.add_argument("--test-only", action="store_true", help="Solo testear (personas ya creadas)")
    parser.add_argument("--cleanup", action="store_true", help="Borrar personas sintéticas")
    parser.add_argument("--dry-run", action="store_true", help="Ver skills sin tocar Supabase")
    args = parser.parse_args()

    print("Cargando datos ESCO...")
    occ_skills, occ_meta, all_skills = load_esco_data()
    print(f"  Ocupaciones: {len(occ_skills)} | Metadata: {len(occ_meta)} | Skills: {len(all_skills)}")

    client = get_supabase_client()

    if args.cleanup:
        cleanup_synthetic(client)
        return

    if args.test_only:
        # Recuperar personas sintéticas existentes
        personas_db = client.table("personas").select("*").like("dni", f"{SYNTHETIC_DNI_PREFIX}%").execute()
        if not personas_db.data:
            print("No hay personas sintéticas. Ejecutá sin --test-only primero.")
            return

        created = []
        for pdb in personas_db.data:
            # Encontrar la definición original
            p_def = next((p for p in PERSONAS if p["dni"] == pdb["dni"]), None)
            if not p_def:
                continue
            perfil = client.table("perfiles").select("id").eq("persona_id", pdb["id"]).limit(1).execute()
            perfil_id = perfil.data[0]["id"] if perfil.data else None
            skills = []
            if perfil_id:
                sk = client.table("perfil_skills").select("*").eq("perfil_id", perfil_id).execute()
                skills = sk.data or []
            created.append({
                "persona": p_def,
                "skills": skills,
                "persona_id": pdb["id"],
                "perfil_id": perfil_id,
            })

        results = test_matching(client, created)
        print_comparative_report(results)
        return

    if args.dry_run:
        created = create_personas_and_skills(None, occ_skills, occ_meta, all_skills, dry_run=True)
        print(f"\n[DRY-RUN] Se crearían {len(created)} personas con "
              f"{sum(len(c['skills']) for c in created)} skills en total.")
        return

    # Limpiar anteriores si existen
    existing = client.table("personas").select("id", count="exact") \
        .like("dni", f"{SYNTHETIC_DNI_PREFIX}%").limit(0).execute()
    if existing.count and existing.count > 0:
        print(f"\nLimpiando {existing.count} personas sintéticas anteriores...")
        cleanup_synthetic(client)

    # Crear personas + skills
    created = create_personas_and_skills(client, occ_skills, occ_meta, all_skills)
    print(f"\n{'='*60}")
    print(f"  CREADAS: {len(created)} personas con {sum(len(c['skills']) for c in created)} skills")
    print(f"{'='*60}")

    # Testear matching
    results = test_matching(client, created)
    print_comparative_report(results)


if __name__ == "__main__":
    main()
