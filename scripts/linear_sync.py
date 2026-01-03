#!/usr/bin/env python3
"""
Linear Issues Sync - Cache local de issues de Linear

Sincroniza todos los issues del proyecto MOL a .linear/issues.json
para acceso rápido sin depender del MCP.

Uso:
    python scripts/linear_sync.py
    python scripts/linear_sync.py --project "MOL"
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
OUTPUT_FILE = BASE_DIR / ".linear" / "issues.json"

LINEAR_API_URL = "https://api.linear.app/graphql"


def load_config():
    """Carga la configuración de Linear desde config/linear_config.json"""
    if not CONFIG_FILE.exists():
        print(f"ERROR: No se encontró {CONFIG_FILE}")
        print("Crea el archivo con tu API key:")
        print('  {"api_key": "lin_api_..."}')
        sys.exit(1)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    if "api_key" not in config:
        print("ERROR: El archivo de config debe tener 'api_key'")
        sys.exit(1)

    return config


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


def get_team_id(api_key: str, team_key: str = "MOL") -> str:
    """Obtiene el ID del team por su key"""
    query = """
    query GetTeam($key: String!) {
        team(key: $key) {
            id
            name
            key
        }
    }
    """

    # Linear no soporta buscar por key directamente, obtenemos todos los teams
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
        if team["key"].upper() == team_key.upper():
            return team["id"]

    raise Exception(f"No se encontró el team con key '{team_key}'")


def get_all_issues(api_key: str, team_id: str) -> list:
    """Obtiene todos los issues del team"""
    query = """
    query GetIssues($teamId: String!, $after: String) {
        team(id: $teamId) {
            issues(first: 100, after: $after) {
                pageInfo {
                    hasNextPage
                    endCursor
                }
                nodes {
                    id
                    identifier
                    title
                    description
                    priority
                    priorityLabel
                    state {
                        id
                        name
                        type
                    }
                    labels {
                        nodes {
                            id
                            name
                            color
                        }
                    }
                    parent {
                        id
                        identifier
                        title
                    }
                    project {
                        id
                        name
                    }
                    assignee {
                        id
                        name
                        email
                    }
                    createdAt
                    updatedAt
                    completedAt
                    estimate
                    url
                }
            }
        }
    }
    """

    all_issues = []
    cursor = None

    while True:
        variables = {"teamId": team_id}
        if cursor:
            variables["after"] = cursor

        data = graphql_query(api_key, query, variables)
        issues_data = data["team"]["issues"]

        for issue in issues_data["nodes"]:
            # Simplificar estructura
            simplified = {
                "id": issue["id"],
                "identifier": issue["identifier"],  # MOL-XX
                "title": issue["title"],
                "description": issue["description"],
                "priority": issue["priority"],
                "priority_label": issue["priorityLabel"],
                "status": issue["state"]["name"] if issue["state"] else None,
                "status_type": issue["state"]["type"] if issue["state"] else None,
                "labels": [l["name"] for l in issue["labels"]["nodes"]],
                "epic": issue["parent"]["identifier"] if issue["parent"] else None,
                "epic_title": issue["parent"]["title"] if issue["parent"] else None,
                "project": issue["project"]["name"] if issue["project"] else None,
                "assignee": issue["assignee"]["name"] if issue["assignee"] else None,
                "created_at": issue["createdAt"],
                "updated_at": issue["updatedAt"],
                "completed_at": issue["completedAt"],
                "estimate": issue["estimate"],
                "url": issue["url"]
            }
            all_issues.append(simplified)

        if not issues_data["pageInfo"]["hasNextPage"]:
            break
        cursor = issues_data["pageInfo"]["endCursor"]

    return all_issues


def get_workflow_states(api_key: str, team_id: str) -> list:
    """Obtiene los estados del workflow del team"""
    query = """
    query GetStates($teamId: String!) {
        team(id: $teamId) {
            states {
                nodes {
                    id
                    name
                    type
                    position
                }
            }
        }
    }
    """

    data = graphql_query(api_key, query, {"teamId": team_id})
    return data["team"]["states"]["nodes"]


def sync_issues(team_key: str = "MOL"):
    """Sincroniza todos los issues del team a JSON local"""
    print(f"Sincronizando issues de Linear ({team_key})...")

    config = load_config()
    api_key = config["api_key"]

    # Obtener team ID
    print("  - Buscando team...")
    team_id = get_team_id(api_key, team_key)
    print(f"    Team ID: {team_id}")

    # Obtener workflow states
    print("  - Obteniendo estados del workflow...")
    states = get_workflow_states(api_key, team_id)

    # Obtener issues
    print("  - Descargando issues...")
    issues = get_all_issues(api_key, team_id)
    print(f"    {len(issues)} issues encontrados")

    # Crear estructura de salida
    output = {
        "synced_at": datetime.now().isoformat(),
        "team": team_key,
        "total_issues": len(issues),
        "workflow_states": states,
        "issues": sorted(issues, key=lambda x: x["identifier"])
    }

    # Crear directorio si no existe
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Guardar
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nGuardado en: {OUTPUT_FILE}")
    print(f"Total: {len(issues)} issues")

    # Resumen por status
    status_count = {}
    for issue in issues:
        status = issue["status"] or "Sin estado"
        status_count[status] = status_count.get(status, 0) + 1

    print("\nPor estado:")
    for status, count in sorted(status_count.items()):
        print(f"  - {status}: {count}")

    return output


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sincroniza issues de Linear a cache local")
    parser.add_argument("--project", "-p", default="MOL", help="Key del team/proyecto (default: MOL)")

    args = parser.parse_args()
    sync_issues(args.project)
