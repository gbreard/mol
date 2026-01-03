#!/usr/bin/env python3
"""
Linear Issue Creator - Crea issues desde MOL_LINEAR_ISSUES_V3.md

Parsea el archivo de documentacion y crea issues en Linear.
Solo crea issues que no existen (verifica por identifier).

Uso:
    python scripts/linear_create_issues.py --priority=high
    python scripts/linear_create_issues.py --all
    python scripts/linear_create_issues.py --dry-run
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

import requests

# Configuracion
BASE_DIR = Path(__file__).parent.parent
CONFIG_FILE = BASE_DIR / "config" / "linear_config.json"
ISSUES_FILE = BASE_DIR / "docs" / "MOL_LINEAR_ISSUES_V3.md"
CACHE_FILE = BASE_DIR / ".linear" / "issues.json"
LOG_FILE = BASE_DIR / ".linear" / "create_log.txt"

LINEAR_API_URL = "https://api.linear.app/graphql"


def load_config():
    """Carga la configuracion de Linear"""
    if not CONFIG_FILE.exists():
        print(f"ERROR: No se encontro {CONFIG_FILE}")
        sys.exit(1)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def graphql_query(api_key: str, query: str, variables: dict = None):
    """Ejecuta una query GraphQL en Linear"""
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(LINEAR_API_URL, headers=headers, json=payload)
    response.raise_for_status()

    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")

    return data["data"]


def get_team_id(api_key: str) -> str:
    """Obtiene el ID del team MOL"""
    query = """
    query {
        teams {
            nodes {
                id
                name
                key
            }
        }
    }
    """
    data = graphql_query(api_key, query)
    for team in data["teams"]["nodes"]:
        if team["key"].upper() == "MOL":
            return team["id"]
    raise Exception("No se encontro el team MOL")


def get_existing_issues(api_key: str, team_id: str) -> set:
    """Obtiene los identifiers de issues existentes"""
    query = """
    query GetIssues($teamId: String!, $after: String) {
        team(id: $teamId) {
            issues(first: 100, after: $after) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                nodes {
                    identifier
                }
            }
        }
    }
    """

    identifiers = set()
    cursor = None

    while True:
        variables = {"teamId": team_id}
        if cursor:
            variables["after"] = cursor

        data = graphql_query(api_key, query, variables)
        issues_data = data["team"]["issues"]

        for issue in issues_data["nodes"]:
            identifiers.add(issue["identifier"])

        if not issues_data["pageInfo"]["hasNextPage"]:
            break
        cursor = issues_data["pageInfo"]["endCursor"]

    return identifiers


def get_workflow_states(api_key: str, team_id: str) -> dict:
    """Obtiene los estados del workflow"""
    query = """
    query GetStates($teamId: String!) {
        team(id: $teamId) {
            states {
                nodes {
                    id
                    name
                    type
                }
            }
        }
    }
    """
    data = graphql_query(api_key, query, {"teamId": team_id})
    states = {}
    for state in data["team"]["states"]["nodes"]:
        states[state["name"].lower()] = state["id"]
        states[state["type"]] = state["id"]
    return states


def get_labels(api_key: str, team_id: str) -> dict:
    """Obtiene los labels del team"""
    query = """
    query GetLabels($teamId: String!) {
        team(id: $teamId) {
            labels {
                nodes {
                    id
                    name
                }
            }
        }
    }
    """
    data = graphql_query(api_key, query, {"teamId": team_id})
    return {label["name"].lower(): label["id"] for label in data["team"]["labels"]["nodes"]}


def parse_issues_markdown(filepath: Path) -> list:
    """Parsea el archivo markdown y extrae issues"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    issues = []

    # Patron para encontrar issues: ## MOL-XX: Titulo
    issue_pattern = r"## (MOL-\d+): (.+?)(?=\n)"
    matches = list(re.finditer(issue_pattern, content))

    for i, match in enumerate(matches):
        identifier = match.group(1)
        title = match.group(2).strip()

        # Obtener el contenido hasta el siguiente issue o fin del archivo
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section = content[start:end]

        # Extraer prioridad
        priority = 3  # Default: medium
        if "Alta" in section or "high" in section.lower():
            priority = 2
        elif "Baja" in section or "low" in section.lower():
            priority = 4
        elif "Urgente" in section or "urgent" in section.lower():
            priority = 1

        # Extraer labels
        labels_match = re.search(r"### Labels:\s*`([^`]+)`", section)
        if not labels_match:
            labels_match = re.search(r"\*\*Labels:\*\*\s*`([^`]+)`", section)

        labels = []
        if labels_match:
            labels = [l.strip() for l in labels_match.group(1).split(",")]

        # Limpiar descripcion (todo el contenido de la seccion)
        description = section.strip()

        # Detectar si ya esta completado
        if "Estado: " in section and "Completado" in section:
            continue

        issues.append({
            "identifier": identifier,
            "title": title,
            "description": description,
            "priority": priority,
            "labels": labels
        })

    return issues


def create_issue(api_key: str, team_id: str, issue: dict, states: dict, labels: dict, dry_run: bool = False):
    """Crea un issue en Linear"""

    # Mapear labels a IDs
    label_ids = []
    for label in issue.get("labels", []):
        label_lower = label.lower()
        if label_lower in labels:
            label_ids.append(labels[label_lower])

    if dry_run:
        print(f"  [DRY-RUN] Crearia: {issue['identifier']}: {issue['title']}")
        print(f"            Priority: {issue['priority']}, Labels: {issue['labels']}")
        return None

    mutation = """
    mutation CreateIssue($input: IssueCreateInput!) {
        issueCreate(input: $input) {
            success
            issue {
                id
                identifier
                title
                url
            }
        }
    }
    """

    variables = {
        "input": {
            "teamId": team_id,
            "title": f"{issue['identifier']}: {issue['title']}",
            "description": issue["description"],
            "priority": issue["priority"],
            "stateId": states.get("backlog", states.get("unstarted"))
        }
    }

    if label_ids:
        variables["input"]["labelIds"] = label_ids

    try:
        data = graphql_query(api_key, mutation, variables)
        if data["issueCreate"]["success"]:
            created = data["issueCreate"]["issue"]
            print(f"  Creado: {created['identifier']}: {issue['title']}")
            return created
        else:
            print(f"  ERROR: No se pudo crear {issue['identifier']}")
            return None
    except Exception as e:
        print(f"  ERROR creando {issue['identifier']}: {e}")
        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Crea issues en Linear desde MOL_LINEAR_ISSUES_V3.md")
    parser.add_argument("--priority", choices=["high", "medium", "low", "all"], default="all",
                        help="Filtrar por prioridad")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar que se crearia")
    parser.add_argument("--force", action="store_true", help="Crear aunque ya exista")

    args = parser.parse_args()

    print("=== Linear Issue Creator ===\n")

    # Cargar config
    config = load_config()
    api_key = config["api_key"]

    # Obtener team
    print("Obteniendo team MOL...")
    team_id = get_team_id(api_key)

    # Obtener issues existentes
    print("Verificando issues existentes...")
    existing = get_existing_issues(api_key, team_id)
    print(f"  {len(existing)} issues existentes\n")

    # Obtener states y labels
    states = get_workflow_states(api_key, team_id)
    labels = get_labels(api_key, team_id)

    # Parsear markdown
    print(f"Parseando {ISSUES_FILE}...")
    issues = parse_issues_markdown(ISSUES_FILE)
    print(f"  {len(issues)} issues encontrados\n")

    # Filtrar por prioridad
    priority_map = {"high": 2, "medium": 3, "low": 4}
    if args.priority != "all":
        target_priority = priority_map[args.priority]
        issues = [i for i in issues if i["priority"] <= target_priority]
        print(f"  {len(issues)} issues con prioridad {args.priority} o mayor\n")

    # Filtrar existentes
    if not args.force:
        issues = [i for i in issues if i["identifier"] not in existing]
        print(f"  {len(issues)} issues nuevos para crear\n")

    if not issues:
        print("No hay issues nuevos para crear.")
        return

    # Crear issues
    print("Creando issues...")
    created = 0
    for issue in issues:
        result = create_issue(api_key, team_id, issue, states, labels, args.dry_run)
        if result:
            created += 1

    print(f"\n{'Simulacion' if args.dry_run else 'Creacion'} completada: {created}/{len(issues)} issues")

    # Log
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - Created {created} issues (dry_run={args.dry_run})\n")


if __name__ == "__main__":
    main()
