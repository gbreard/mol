#!/usr/bin/env python3
"""
Linear Issue Update - Actualiza issues en Linear

Actualiza un issue específico en Linear y el cache local.

Uso:
    python scripts/linear_update.py MOL-31 --status=done
    python scripts/linear_update.py MOL-31 --status=done --comment="Implementado en v8.4"
    python scripts/linear_update.py MOL-31 --comment="Nota sin cambiar estado"
    python scripts/linear_update.py MOL-31 --priority=high
    python scripts/linear_update.py MOL-31 --assignee=me

Estados disponibles (dependen del workflow del team):
    backlog, todo, in_progress, in_review, done, canceled
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

# Configuración
BASE_DIR = Path(__file__).parent.parent
CONFIG_FILE = BASE_DIR / "config" / "linear_config.json"
CACHE_FILE = BASE_DIR / ".linear" / "issues.json"

LINEAR_API_URL = "https://api.linear.app/graphql"

# Mapeo de estados comunes a tipos de Linear
STATUS_ALIASES = {
    "backlog": "backlog",
    "todo": "unstarted",
    "in_progress": "started",
    "in-progress": "started",
    "inprogress": "started",
    "started": "started",
    "in_review": "started",
    "review": "started",
    "done": "completed",
    "completed": "completed",
    "canceled": "canceled",
    "cancelled": "canceled"
}

PRIORITY_MAP = {
    "urgent": 1,
    "high": 2,
    "medium": 3,
    "normal": 3,
    "low": 4,
    "none": 0,
    "no": 0
}


def load_config():
    """Carga la configuración de Linear"""
    if not CONFIG_FILE.exists():
        print(f"ERROR: No se encontró {CONFIG_FILE}")
        print("Ejecuta primero: python scripts/linear_sync.py")
        sys.exit(1)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_cache():
    """Carga el cache de issues"""
    if not CACHE_FILE.exists():
        print(f"ERROR: No se encontró el cache en {CACHE_FILE}")
        print("Ejecuta primero: python scripts/linear_sync.py")
        sys.exit(1)

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(cache):
    """Guarda el cache actualizado"""
    cache["synced_at"] = datetime.now().isoformat()
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


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


def find_state_id(api_key: str, team_id: str, status_name: str) -> str:
    """Encuentra el ID del estado por nombre o tipo"""
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
    states = data["team"]["states"]["nodes"]

    status_lower = status_name.lower()

    # Buscar por nombre exacto
    for state in states:
        if state["name"].lower() == status_lower:
            return state["id"]

    # Buscar por tipo usando aliases
    target_type = STATUS_ALIASES.get(status_lower, status_lower)
    for state in states:
        if state["type"] == target_type:
            return state["id"]

    # Listar estados disponibles
    available = [f"{s['name']} ({s['type']})" for s in states]
    raise Exception(f"Estado '{status_name}' no encontrado. Disponibles: {', '.join(available)}")


def get_team_id_from_issue(api_key: str, identifier: str) -> str:
    """Obtiene el team ID a partir del identifier del issue"""
    query = """
    query GetIssue($identifier: String!) {
        issue(id: $identifier) {
            id
            team {
                id
            }
        }
    }
    """

    # Linear usa el identifier para buscar
    # Primero buscamos por identifier
    search_query = """
    query SearchIssue($filter: IssueFilter!) {
        issues(filter: $filter) {
            nodes {
                id
                identifier
                team {
                    id
                }
            }
        }
    }
    """

    # Extraer team key y número
    parts = identifier.split("-")
    if len(parts) != 2:
        raise Exception(f"Identifier inválido: {identifier}. Formato esperado: MOL-XX")

    team_key = parts[0]
    number = int(parts[1])

    # Buscar el team
    teams_query = """
    query {
        teams {
            nodes {
                id
                key
            }
        }
    }
    """

    data = graphql_query(api_key, teams_query)
    team_id = None
    for team in data["teams"]["nodes"]:
        if team["key"].upper() == team_key.upper():
            team_id = team["id"]
            break

    if not team_id:
        raise Exception(f"Team '{team_key}' no encontrado")

    return team_id


def get_issue_id(api_key: str, identifier: str) -> str:
    """Obtiene el ID interno del issue por su identifier (MOL-XX)"""
    # Buscar en issues del team
    parts = identifier.split("-")
    team_key = parts[0]
    number = int(parts[1])

    query = """
    query GetIssueByNumber($teamKey: String!, $number: Float!) {
        issueVcsBranchSearch(branchName: $teamKey) {
            id
        }
    }
    """

    # Usar búsqueda por filter
    search_query = """
    query SearchIssues($filter: IssueFilter!) {
        issues(filter: $filter, first: 1) {
            nodes {
                id
                identifier
            }
        }
    }
    """

    # El filtro correcto usa number
    data = graphql_query(api_key, search_query, {
        "filter": {
            "number": {"eq": number},
            "team": {"key": {"eq": team_key}}
        }
    })

    if not data["issues"]["nodes"]:
        raise Exception(f"Issue {identifier} no encontrado")

    return data["issues"]["nodes"][0]["id"]


def update_issue(api_key: str, issue_id: str, updates: dict) -> dict:
    """Actualiza un issue en Linear"""
    query = """
    mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
        issueUpdate(id: $id, input: $input) {
            success
            issue {
                id
                identifier
                title
                state {
                    name
                }
                priority
                priorityLabel
            }
        }
    }
    """

    data = graphql_query(api_key, query, {"id": issue_id, "input": updates})

    if not data["issueUpdate"]["success"]:
        raise Exception("Error al actualizar el issue")

    return data["issueUpdate"]["issue"]


def add_comment(api_key: str, issue_id: str, body: str) -> dict:
    """Agrega un comentario a un issue"""
    query = """
    mutation CreateComment($issueId: String!, $body: String!) {
        commentCreate(input: {issueId: $issueId, body: $body}) {
            success
            comment {
                id
                body
                createdAt
            }
        }
    }
    """

    data = graphql_query(api_key, query, {"issueId": issue_id, "body": body})

    if not data["commentCreate"]["success"]:
        raise Exception("Error al crear el comentario")

    return data["commentCreate"]["comment"]


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Actualiza un issue en Linear",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python linear_update.py MOL-31 --status=done
    python linear_update.py MOL-31 --status=in_progress --comment="Comenzando"
    python linear_update.py MOL-31 --priority=high
        """
    )

    parser.add_argument("identifier", help="Identifier del issue (ej: MOL-31)")
    parser.add_argument("--status", "-s", help="Nuevo estado (backlog, todo, in_progress, done, canceled)")
    parser.add_argument("--comment", "-c", help="Comentario a agregar")
    parser.add_argument("--priority", "-p", help="Prioridad (urgent, high, medium, low, none)")
    parser.add_argument("--title", "-t", help="Nuevo título")

    args = parser.parse_args()

    if not any([args.status, args.comment, args.priority, args.title]):
        parser.error("Debes especificar al menos --status, --comment, --priority o --title")

    # Cargar config
    config = load_config()
    api_key = config["api_key"]

    identifier = args.identifier.upper()
    print(f"Actualizando {identifier}...")

    try:
        # Obtener IDs
        team_id = get_team_id_from_issue(api_key, identifier)
        issue_id = get_issue_id(api_key, identifier)

        # Preparar updates
        updates = {}

        if args.status:
            state_id = find_state_id(api_key, team_id, args.status)
            updates["stateId"] = state_id
            print(f"  - Estado: {args.status}")

        if args.priority:
            priority_value = PRIORITY_MAP.get(args.priority.lower())
            if priority_value is None:
                print(f"Prioridad inválida: {args.priority}")
                print(f"Opciones: {', '.join(PRIORITY_MAP.keys())}")
                sys.exit(1)
            updates["priority"] = priority_value
            print(f"  - Prioridad: {args.priority}")

        if args.title:
            updates["title"] = args.title
            print(f"  - Título: {args.title}")

        # Aplicar updates
        if updates:
            result = update_issue(api_key, issue_id, updates)
            print(f"\nIssue actualizado: {result['identifier']}")
            print(f"  Estado: {result['state']['name']}")
            print(f"  Prioridad: {result['priorityLabel']}")

        # Agregar comentario
        if args.comment:
            comment = add_comment(api_key, issue_id, args.comment)
            print(f"\nComentario agregado: {comment['body'][:50]}...")

        # Actualizar cache local
        cache = load_cache()
        for issue in cache["issues"]:
            if issue["identifier"] == identifier:
                if args.status:
                    issue["status"] = args.status
                if args.priority:
                    issue["priority_label"] = args.priority
                if args.title:
                    issue["title"] = args.title
                issue["updated_at"] = datetime.now().isoformat()
                break

        save_cache(cache)
        print("\nCache local actualizado")

    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
