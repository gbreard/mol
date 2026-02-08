#!/bin/bash
# ============================================================
# Worktree Session Manager para Claude Code
# ============================================================
#
# Problema: Dos sesiones de Claude en el mismo directorio se
# pisan los branches. Solución: cada sesión en su worktree.
#
# Uso:
#   # Crear sesión nueva en un branch existente:
#   ./scripts/worktree-session.sh create feature/admin-arquitectura
#
#   # Crear sesión nueva con branch nuevo desde main:
#   ./scripts/worktree-session.sh new feature/mi-nuevo-feature
#
#   # Listar sesiones activas:
#   ./scripts/worktree-session.sh list
#
#   # Cerrar sesión (borra worktree, NO borra el branch):
#   ./scripts/worktree-session.sh remove feature/admin-arquitectura
#
# Cada sesión de Claude Code se abre en su propia carpeta:
#   /mnt/d/OEDE/Webscrapping              ← Sesión principal
#   /mnt/d/OEDE/Webscrapping-admin        ← Sesión 2
#   /mnt/d/OEDE/Webscrapping-mi-feature   ← Sesión 3
#
# ============================================================

set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PARENT_DIR="$(dirname "$BASE_DIR")"
PROJECT_NAME="$(basename "$BASE_DIR")"

branch_to_dirname() {
    # feature/admin-arquitectura → Webscrapping-admin-arquitectura
    local branch="$1"
    local short="${branch##*/}"  # Remove prefix (feature/, fix/, etc.)
    echo "${PROJECT_NAME}-${short}"
}

cmd_create() {
    local branch="${1:?Uso: $0 create <branch-name>}"
    local dirname
    dirname="$(branch_to_dirname "$branch")"
    local worktree_path="${PARENT_DIR}/${dirname}"

    if [ -d "$worktree_path" ]; then
        echo "Ya existe: $worktree_path"
        echo "Usá 'cd $worktree_path' para entrar"
        exit 0
    fi

    echo "Creando worktree para '$branch' en $worktree_path..."
    git -C "$BASE_DIR" worktree add "$worktree_path" "$branch"
    echo ""
    echo "Listo. Para usar en Claude Code:"
    echo "  cd $worktree_path"
    echo ""
    echo "Para cerrar cuando termines:"
    echo "  $0 remove $branch"
}

cmd_new() {
    local branch="${1:?Uso: $0 new <branch-name>}"
    local base="${2:-main}"
    local dirname
    dirname="$(branch_to_dirname "$branch")"
    local worktree_path="${PARENT_DIR}/${dirname}"

    if [ -d "$worktree_path" ]; then
        echo "Ya existe: $worktree_path"
        exit 1
    fi

    echo "Creando branch '$branch' desde '$base' con worktree..."
    git -C "$BASE_DIR" worktree add -b "$branch" "$worktree_path" "$base"
    echo ""
    echo "Listo. Para usar en Claude Code:"
    echo "  cd $worktree_path"
}

cmd_list() {
    echo "Sesiones activas:"
    echo ""
    git -C "$BASE_DIR" worktree list
    echo ""
}

cmd_remove() {
    local branch="${1:?Uso: $0 remove <branch-name>}"
    local dirname
    dirname="$(branch_to_dirname "$branch")"
    local worktree_path="${PARENT_DIR}/${dirname}"

    if [ ! -d "$worktree_path" ]; then
        echo "No existe: $worktree_path"
        git -C "$BASE_DIR" worktree prune
        exit 0
    fi

    echo "Eliminando worktree $worktree_path..."
    git -C "$BASE_DIR" worktree remove "$worktree_path" --force 2>/dev/null || {
        rm -rf "$worktree_path" 2>/dev/null
        git -C "$BASE_DIR" worktree prune
    }
    echo "Worktree eliminado. Branch '$branch' sigue existiendo."
}

case "${1:-help}" in
    create) cmd_create "${2:-}" ;;
    new)    cmd_new "${2:-}" "${3:-main}" ;;
    list)   cmd_list ;;
    remove) cmd_remove "${2:-}" ;;
    *)
        echo "Uso: $0 {create|new|list|remove} [branch]"
        echo ""
        echo "  create <branch>        Worktree para branch existente"
        echo "  new <branch> [base]    Crear branch + worktree (base=main)"
        echo "  list                   Listar sesiones activas"
        echo "  remove <branch>        Cerrar sesión (no borra branch)"
        ;;
esac
