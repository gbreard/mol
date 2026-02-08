"""
Generador automático de dashboard_architecture.json

Lee fuentes de verdad reales (pages, API routes, configs, learnings.yaml)
y genera el JSON que consume /admin/arquitectura.

Uso:
    python scripts/generate_architecture_json.py           # genera archivo
    python scripts/generate_architecture_json.py --dry-run  # stdout sin escribir
    python scripts/generate_architecture_json.py --check    # verifica si está al día

Version: 1.0
Fecha: 2026-02-08
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

# =====================================================================
# PATHS
# =====================================================================

BASE_DIR = Path(__file__).parent.parent
DASHBOARD_DIR = BASE_DIR / "fase3_dashboard" / "mol-dashboard"
APP_DIR = DASHBOARD_DIR / "app"
OUTPUT_PATH = DASHBOARD_DIR / "public" / "data" / "dashboard_architecture.json"
MANIFEST_PATH = DASHBOARD_DIR / "public" / "data" / "route_manifest.json"
LEARNINGS_PATH = BASE_DIR / ".ai" / "learnings.yaml"
CONFIG_DIR = BASE_DIR / "config"
SOURCES_DIR = BASE_DIR / "01_sources"
SCHEDULER_PATH = BASE_DIR / "run_scheduler.py"

# Reutilizar load_config_counts de sync_learnings.py
sys.path.insert(0, str(BASE_DIR / "scripts"))
try:
    from sync_learnings import load_config_counts
except ImportError:
    def load_config_counts() -> dict[str, int]:
        """Fallback si sync_learnings no está disponible."""
        return {}


# =====================================================================
# MANIFEST
# =====================================================================

def load_manifest() -> dict[str, Any]:
    """Lee route_manifest.json con metadata manual."""
    if not MANIFEST_PATH.exists():
        print(f"[WARN] Manifest no encontrado: {MANIFEST_PATH}", file=sys.stderr)
        return {"pages": {}, "apiRoutes": {}, "connections_manual": []}

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# =====================================================================
# PAGE DISCOVERY
# =====================================================================

def _path_from_filesystem(page_file: Path) -> str:
    """Convierte filesystem path a route path.

    app/page.tsx → /
    app/admin/skills/page.tsx → /admin/skills
    app/checkout/exito/page.tsx → /checkout/exito
    """
    rel = page_file.parent.relative_to(APP_DIR)
    parts = [p for p in rel.parts if p != "."]
    return "/" + "/".join(parts) if parts else "/"


def _generate_id(path: str) -> str:
    """Genera un ID slug desde el path.

    / → home
    /admin/skills → admin-skills
    /checkout/exito → checkout-exito
    /auth/callback → auth-callback
    """
    if path == "/":
        return "landing"
    return path.strip("/").replace("/", "-").replace("[", "").replace("]", "")


def _generate_label(path: str) -> str:
    """Fallback label cuando no hay manifest.

    /admin/skills → Admin Skills
    /checkout/exito → Checkout Exito
    """
    if path == "/":
        return "Landing"
    parts = path.strip("/").split("/")
    return " ".join(p.replace("-", " ").replace("_", " ").title() for p in parts)


def _infer_type(path: str) -> str:
    """Infiere tipo de página desde el path."""
    if path.startswith("/admin"):
        return "admin"
    if path.startswith("/dashboard"):
        return "dashboard"
    if path.startswith("/checkout"):
        return "checkout"
    if path.startswith("/cuenta"):
        return "account"
    if path in ("/login", "/registro", "/auth/callback"):
        return "auth"
    if path in ("/", "/skills", "/precios", "/informes"):
        return "public"
    return "authenticated"


def _extract_page_info(page_file: Path) -> dict[str, Any]:
    """Extrae info de un page.tsx: imports, fetch calls, 'use client'."""
    content = page_file.read_text(encoding="utf-8", errors="replace")

    # Rendering mode
    is_client = "'use client'" in content or '"use client"' in content

    components: list[str] = []

    # Named imports: import { Foo, Bar } from '@/components/...'
    named_import_re = re.compile(
        r"""import\s+\{([^}]+)\}\s+from\s+['"]@/components/(?!ui/)([^'"]+)['"]"""
    )
    for match in named_import_re.finditer(content):
        names = [n.strip().split(" as ")[-1].strip() for n in match.group(1).split(",")]
        for name in names:
            if name and name not in components and name[0].isupper():
                components.append(name)

    # Default imports de componentes
    default_import_re = re.compile(
        r"""import\s+(\w+)\s+from\s+['"]@/components/(?!ui/)([^'"]+)['"]"""
    )
    for match in default_import_re.finditer(content):
        name = match.group(1)
        if name not in components and name[0].isupper():
            components.append(name)

    # Relative component imports (./components/ or ./_components/)
    rel_comp_re = re.compile(
        r"""import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['"]\.\/(?:_?components)\/([^'"]+)['"]"""
    )
    for match in rel_comp_re.finditer(content):
        if match.group(1):
            names = [n.strip().split(" as ")[-1].strip() for n in match.group(1).split(",")]
            for name in names:
                if name and name not in components and name[0].isupper():
                    components.append(name)
        elif match.group(2):
            name = match.group(2)
            if name not in components and name[0].isupper():
                components.append(name)

    # Data sources: fetch('/api/...') and fetch('/data/...')
    data_sources: list[str] = []
    fetch_re = re.compile(r"""fetch\s*\(\s*['"`](/(?:api|data)/[^'"`\s)]+)""")
    for match in fetch_re.finditer(content):
        src = match.group(1)
        if src not in data_sources:
            data_sources.append(src)

    # Supabase .from('tabla')
    supabase_re = re.compile(r"""\.from\s*\(\s*['"](\w+)['"]""")
    for match in supabase_re.finditer(content):
        table = match.group(1)
        if table not in data_sources:
            data_sources.append(table)

    return {
        "rendering": "client" if is_client else "server",
        "components": components,
        "dataSource": data_sources,
    }


def discover_pages(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Escanea app/**/page.tsx y genera la lista de páginas."""
    pages = []
    manifest_pages = manifest.get("pages", {})
    found_paths: set[str] = set()

    for page_file in sorted(APP_DIR.rglob("page.tsx")):
        path = _path_from_filesystem(page_file)
        found_paths.add(path)
        info = _extract_page_info(page_file)

        # Manifest overrides para label, description, type
        m = manifest_pages.get(path, {})
        label = m.get("label") or _generate_label(path)
        description = m.get("description", "")
        page_type = m.get("type") or _infer_type(path)

        pages.append({
            "id": _generate_id(path),
            "path": path,
            "label": label,
            "type": page_type,
            "description": description,
            "rendering": info["rendering"],
            "components": info["components"],
            "dataSource": info["dataSource"],
        })

    # Warn sobre rutas en manifest sin page.tsx
    for manifest_path in manifest_pages:
        if manifest_path not in found_paths:
            print(f"[WARN] Ruta en manifest sin page.tsx: {manifest_path}", file=sys.stderr)

    return pages


# =====================================================================
# API ROUTE DISCOVERY
# =====================================================================

def _api_path_from_filesystem(route_file: Path) -> str:
    """Convierte filesystem path a API route path.

    app/api/admin/stats/route.ts → /api/admin/stats
    app/auth/callback/route.ts → /auth/callback
    """
    rel = route_file.parent.relative_to(APP_DIR)
    return "/" + "/".join(rel.parts)


def _extract_route_info(route_file: Path) -> dict[str, Any]:
    """Extrae info de un route.ts: HTTP methods, tablas Supabase."""
    content = route_file.read_text(encoding="utf-8", errors="replace")

    # HTTP methods
    methods: list[str] = []
    method_re = re.compile(r"""export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH)""")
    for match in method_re.finditer(content):
        m = match.group(1)
        if m not in methods:
            methods.append(m)

    # Supabase tables
    tables: list[str] = []
    supabase_re = re.compile(r"""\.from\s*\(\s*['"](\w+)['"]""")
    for match in supabase_re.finditer(content):
        table = match.group(1)
        if table not in tables:
            tables.append(table)

    return {
        "methods": methods,
        "tables": tables,
    }


def discover_api_routes(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Escanea app/api/**/route.ts y app/auth/**/route.ts."""
    routes = []
    manifest_api = manifest.get("apiRoutes", {})

    for route_file in sorted(APP_DIR.rglob("route.ts")):
        path = _api_path_from_filesystem(route_file)
        info = _extract_route_info(route_file)

        m = manifest_api.get(path, {})
        label = m.get("label") or _generate_label(path)
        description = m.get("description", "")
        method_str = "/".join(info["methods"]) if info["methods"] else "GET"

        routes.append({
            "id": _generate_id(path),
            "path": path,
            "method": method_str,
            "description": description,
            "tables": info["tables"],
            "usedBy": [],  # se llena en extract_connections
        })

    return routes


# =====================================================================
# CONNECTIONS
# =====================================================================

def extract_connections(
    pages: list[dict[str, Any]],
    api_routes: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    """Auto-detecta conexiones + agrega las manuales del manifest.

    Dedup by (from, to, type) — manual labels override auto-detected.
    """
    # key: (from, to, type) → label
    conn_map: dict[tuple[str, str, str], str] = {}
    api_paths = {r["path"] for r in api_routes}
    page_paths = {p["path"] for p in pages}

    for page in pages:
        page_path = page["path"]

        # Conexiones data: page → API (desde dataSource)
        for src in page["dataSource"]:
            if src.startswith("/api/"):
                matched = _match_api_path(src, api_paths)
                if matched:
                    key = (page_path, matched, "data")
                    if key not in conn_map:
                        conn_map[key] = f"Fetch {matched.split('/')[-1]}"

        # Conexiones navigation: scan page files for href="/..."
        page_file = _find_page_file(page_path)
        if page_file and page_file.exists():
            content = page_file.read_text(encoding="utf-8", errors="replace")
            href_re = re.compile(r"""href\s*=\s*["'](/[^"'\s{]+)["']""")
            for match in href_re.finditer(content):
                target = match.group(1)
                if target in page_paths and target != page_path:
                    key = (page_path, target, "navigation")
                    if key not in conn_map:
                        conn_map[key] = ""

    # Manual connections override auto-detected labels
    for mc in manifest.get("connections_manual", []):
        key = (mc["from"], mc["to"], mc["type"])
        conn_map[key] = mc.get("label", "")

    # Build result list and populate usedBy
    result = []
    api_used_by: dict[str, list[str]] = {r["path"]: [] for r in api_routes}

    for (from_path, to_path, conn_type), label in sorted(conn_map.items()):
        result.append({
            "from": from_path,
            "to": to_path,
            "type": conn_type,
            "label": label,
        })
        if to_path in api_used_by and from_path not in api_used_by[to_path]:
            api_used_by[to_path].append(from_path)

    for route in api_routes:
        route["usedBy"] = api_used_by.get(route["path"], [])

    return result


def _match_api_path(fetch_path: str, api_paths: set[str]) -> str | None:
    """Busca match exacto o con query params removidos."""
    # Remover query string
    clean = fetch_path.split("?")[0]
    if clean in api_paths:
        return clean

    # Buscar match con dynamic segments
    for api_path in api_paths:
        if "[" in api_path:
            # Convertir /api/perfil-argentina/[occupation] a regex
            pattern = re.escape(api_path).replace(r"\[", "[^/]+").replace(r"\]", "")
            if re.match(f"^{pattern}$", clean):
                return api_path

    # Buscar prefijo más largo (para /api/x/y que matchea /api/x)
    for api_path in sorted(api_paths, key=len, reverse=True):
        if clean.startswith(api_path):
            return api_path

    return None


def _find_page_file(path: str) -> Path | None:
    """Dado un route path, retorna el page.tsx correspondiente."""
    if path == "/":
        return APP_DIR / "page.tsx"
    rel = path.strip("/")
    return APP_DIR / rel / "page.tsx"


# =====================================================================
# PIPELINE
# =====================================================================

def _parse_versions_from_learnings() -> dict[str, str]:
    """Parsea versiones desde learnings.yaml (sin depender de PyYAML)."""
    versions = {
        "matching": "v3.4",
        "nlp": "v11",
        "skills": "v2.3",
    }
    if not LEARNINGS_PATH.exists():
        return versions

    content = LEARNINGS_PATH.read_text(encoding="utf-8", errors="replace")

    # matching_version: "v3.5.3"
    m = re.search(r'matching_version:\s*"?(v[\d.]+)"?', content)
    if m:
        versions["matching"] = m.group(1)

    return versions


def _discover_scrapers() -> list[dict[str, Any]]:
    """Descubre scrapers desde 01_sources/ y detecta cuáles están activos."""
    # Scrapers conocidos por directorio
    scraper_names = {
        "bumeran": "Bumeran",
        "zonajobs": "ZonaJobs",
        "computrabajo": "Computrabajo",
        "indeed": "Indeed",
        "linkedin": "LinkedIn",
    }

    # Detectar cuáles se importan en run_scheduler.py
    active_scrapers: set[str] = set()
    if SCHEDULER_PATH.exists():
        content = SCHEDULER_PATH.read_text(encoding="utf-8", errors="replace")
        for dirname in scraper_names:
            # Buscar import o sys.path que referencie al scraper
            if dirname in content.lower():
                # Verificar que no esté solo comentado
                for line in content.split("\n"):
                    stripped = line.strip()
                    if dirname in stripped.lower() and not stripped.startswith("#"):
                        active_scrapers.add(dirname)
                        break

    scrapers = []
    if SOURCES_DIR.exists():
        for d in sorted(SOURCES_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_"):
                name = scraper_names.get(d.name, d.name.title())
                scrapers.append({
                    "id": d.name,
                    "name": name,
                    "type": "scraper",
                    "status": "active" if d.name in active_scrapers else "inactive",
                })

    return scrapers


def build_pipeline_section() -> dict[str, Any]:
    """Construye la sección pipeline desde fuentes reales."""
    versions = _parse_versions_from_learnings()
    counts = load_config_counts()
    scrapers = _discover_scrapers()

    phases = [
        {
            "id": "phase1",
            "name": "Adquisición",
            "description": "Scraping de ofertas laborales",
            "components": scrapers,
            "entryPoint": "run_scheduler.py",
            "output": "ofertas (SQLite)",
        },
        {
            "id": "phase2",
            "name": "Procesamiento",
            "description": "NLP, Skills y Matching ESCO",
            "components": [
                {
                    "id": "nlp",
                    "name": f"NLP {versions['nlp']}",
                    "type": "processor",
                    "model": "Qwen2.5:7b",
                },
                {
                    "id": "skills",
                    "name": f"Skills Extractor {versions['skills']}",
                    "type": "processor",
                    "model": "BGE-M3",
                    "count": counts.get("reglas_skills_dual", 0),
                },
                {
                    "id": "matching",
                    "name": f"ESCO Matching {versions['matching']}",
                    "type": "processor",
                    "count": counts.get("reglas_negocio", 0),
                },
                {
                    "id": "validation",
                    "name": "Validación",
                    "type": "processor",
                    "count": counts.get("reglas_validacion", 0),
                },
            ],
            "entryPoint": "run_validated_pipeline.py",
            "output": "ofertas_esco_matching",
        },
        {
            "id": "phase3",
            "name": "Presentación",
            "description": "Sync y Dashboard",
            "components": [
                {"id": "sync", "name": "sync_to_supabase", "type": "sync"},
                {"id": "dashboard", "name": "Dashboard Next.js", "type": "frontend"},
            ],
            "entryPoint": "sync_to_supabase.py",
            "output": "Supabase → Dashboard",
        },
    ]

    return {"phases": phases}


# =====================================================================
# WARNINGS
# =====================================================================

def warn_missing_manifest(
    pages: list[dict[str, Any]],
    api_routes: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> None:
    """Imprime rutas sin entrada en manifest."""
    manifest_pages = manifest.get("pages", {})
    manifest_api = manifest.get("apiRoutes", {})

    missing_pages = [p["path"] for p in pages if p["path"] not in manifest_pages]
    missing_api = [r["path"] for r in api_routes if r["path"] not in manifest_api]

    if missing_pages:
        print(f"[WARN] {len(missing_pages)} páginas sin manifest (usando label auto-generado):", file=sys.stderr)
        for p in missing_pages:
            print(f"  - {p}", file=sys.stderr)

    if missing_api:
        print(f"[WARN] {len(missing_api)} API routes sin manifest:", file=sys.stderr)
        for p in missing_api:
            print(f"  - {p}", file=sys.stderr)


# =====================================================================
# GENERATE
# =====================================================================

def generate() -> dict[str, Any]:
    """Genera el JSON completo de arquitectura."""
    manifest = load_manifest()
    pages = discover_pages(manifest)
    api_routes = discover_api_routes(manifest)
    connections = extract_connections(pages, api_routes, manifest)
    pipeline = build_pipeline_section()

    warn_missing_manifest(pages, api_routes, manifest)

    # Limpiar campo tables de apiRoutes (no está en el schema original)
    for route in api_routes:
        route.pop("tables", None)

    result = {
        "pages": pages,
        "apiRoutes": api_routes,
        "connections": connections,
        "pipeline": pipeline,
        "_meta": {
            "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "generator": "scripts/generate_architecture_json.py",
            "stats": {
                "pages": len(pages),
                "apiRoutes": len(api_routes),
                "connections": len(connections),
                "pipeline_phases": len(pipeline["phases"]),
            },
        },
    }

    return result


# =====================================================================
# CLI
# =====================================================================

def main() -> None:
    args = sys.argv[1:]

    if "--check" in args:
        # Verificar si el archivo está al día
        data = generate()
        if not OUTPUT_PATH.exists():
            print("[FAIL] dashboard_architecture.json no existe")
            sys.exit(1)

        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            current = json.load(f)

        # Comparar sin _meta (timestamp cambia siempre)
        data_clean = {k: v for k, v in data.items() if k != "_meta"}
        current_clean = {k: v for k, v in current.items() if k != "_meta"}

        if json.dumps(data_clean, sort_keys=True) == json.dumps(current_clean, sort_keys=True):
            print("[OK] dashboard_architecture.json está al día")
            sys.exit(0)
        else:
            current_pages = len(current.get("pages", []))
            new_pages = len(data.get("pages", []))
            current_api = len(current.get("apiRoutes", []))
            new_api = len(data.get("apiRoutes", []))
            print(f"[OUTDATED] dashboard_architecture.json necesita regenerarse")
            print(f"  Páginas: {current_pages} → {new_pages}")
            print(f"  API routes: {current_api} → {new_api}")
            sys.exit(1)

    data = generate()

    if "--dry-run" in args:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    # Escribir archivo
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    meta = data["_meta"]["stats"]
    print(f"[OK] Generado {OUTPUT_PATH.name}")
    print(f"  Páginas: {meta['pages']}")
    print(f"  API routes: {meta['apiRoutes']}")
    print(f"  Conexiones: {meta['connections']}")
    print(f"  Pipeline fases: {meta['pipeline_phases']}")


if __name__ == "__main__":
    main()
