#!/bin/bash
# publicar_colegas.sh — [FRENTE M] Publicación del export de colegas al VPS.
#
# Reemplaza la ceremonia artesanal de junio 2026 (subir a mano y después agregarle
# columnas, índices y una tabla curada EN el servidor). Acá el archivo llega hecho:
# todo su contenido sale de scripts/05b_export_definitivo.py.
#
# El ciclo, con el patrón del frente J (scp + sha256 en las dos puntas):
#   verificar local -> espacio remoto -> scp con NOMBRE VERSIONADO -> sha256 remoto
#   == local -> swap del symlink -> rotación de uno -> reporte
#
# GUARDAS:
#   - Nunca se pisa un archivo en caliente: se sube con nombre versionado y recién
#     al final se mueve el symlink. Si alguien está descargando la versión vieja,
#     su descarga sigue viva sobre el inode anterior.
#   - El swap es lo ÚLTIMO y sólo ocurre si el hash remoto coincide. Si difiere, se
#     borra lo subido y se aborta sin tocar el symlink.
#   - Rotación de uno: quedan la actual y la anterior; las más viejas se borran.
#
# Uso:  scripts/ops/publicar_colegas.sh <ruta_local.sqlite> [--dry-run]
#
set -euo pipefail

VPS="root@187.124.150.28"
REMOTE_DIR="/srv/datasette"
LINK="${REMOTE_DIR}/colegas.sqlite"
SSH_OPTS="-o ConnectTimeout=15 -o BatchMode=yes"

LOCAL="${1:-}"
DRY_RUN="${2:-}"

log() { echo "[$(date '+%F %T')] $*"; }
abort() { echo "[$(date '+%F %T')] ABORTA: $*" >&2; exit 1; }

[ -n "$LOCAL" ] || abort "falta la ruta del export local. Uso: $0 <ruta.sqlite> [--dry-run]"
[ -f "$LOCAL" ] || abort "no existe el archivo local: $LOCAL"

BASENAME="$(basename "$LOCAL")"
REMOTE_FILE="${REMOTE_DIR}/${BASENAME}"

# ---------------------------------------------------------------- 1) local
log "verificando archivo local…"
SIZE_BYTES=$(stat -c%s "$LOCAL")
SIZE_MB=$((SIZE_BYTES / 1048576))

# El .sha256 lo escribe el 05b al lado del archivo. Si no está, se calcula.
if [ -f "${LOCAL}.sha256" ]; then
    SHA_LOCAL=$(awk '{print $1}' "${LOCAL}.sha256")
    log "  sha256 (del sidecar): ${SHA_LOCAL}"
else
    SHA_LOCAL=$(sha256sum "$LOCAL" | awk '{print $1}')
    log "  sha256 (calculado):   ${SHA_LOCAL}"
fi

# La época viaja adentro del archivo: se lee de ahí, no se pasa por parámetro.
EPOCA=$(sqlite3 -readonly "file:${LOCAL}?mode=ro" "SELECT epoca FROM _meta_version LIMIT 1;" 2>/dev/null || echo "")
[ -n "$EPOCA" ] || abort "el archivo no tiene _meta_version: no se publica algo sin época"
log "  época: ${EPOCA}  ·  peso: ${SIZE_MB} MB"

# ------------------------------------------------------------- 2) espacio
log "verificando espacio en el VPS…"
AVAIL_KB=$(ssh $SSH_OPTS "$VPS" "df -Pk ${REMOTE_DIR} | awk 'NR==2{print \$4}'")
NEED_KB=$(( (SIZE_BYTES / 1024) * 12 / 10 ))   # 20% de holgura
log "  disponible: $((AVAIL_KB / 1024)) MB  ·  necesario (con holgura): $((NEED_KB / 1024)) MB"
[ "$AVAIL_KB" -ge "$NEED_KB" ] || abort "espacio insuficiente en el VPS"

if [ "$DRY_RUN" = "--dry-run" ]; then
    log "DRY-RUN: hasta acá llega. No se sube nada."
    exit 0
fi

# ------------------------------------------------------------------ 3) scp
log "subiendo con nombre versionado: ${REMOTE_FILE}"
scp $SSH_OPTS "$LOCAL" "${VPS}:${REMOTE_FILE}"

# ------------------------------------------------------- 4) hash remoto
log "verificando hash en el remoto…"
SHA_REMOTO=$(ssh $SSH_OPTS "$VPS" "sha256sum '${REMOTE_FILE}' | awk '{print \$1}'")
log "  remoto: ${SHA_REMOTO}"
if [ "$SHA_LOCAL" != "$SHA_REMOTO" ]; then
    log "hash NO coincide — borrando lo subido y abortando SIN tocar el symlink"
    ssh $SSH_OPTS "$VPS" "rm -f '${REMOTE_FILE}'"
    abort "sha256 difiere (local ${SHA_LOCAL} vs remoto ${SHA_REMOTO})"
fi
log "  ✓ hash idéntico en las dos puntas"

# --------------------------------------------------- 5) swap del symlink
# Primera corrida: colegas.sqlite todavía es un archivo regular (el de junio).
# Se lo preserva con nombre versionado para que entre en la rotación como
# "la anterior", y recién ahí se lo reemplaza por el symlink.
log "moviendo el symlink…"
ssh $SSH_OPTS "$VPS" "bash -s" <<REMOTO
set -euo pipefail
cd '${REMOTE_DIR}'
if [ -f 'colegas.sqlite' ] && [ ! -L 'colegas.sqlite' ]; then
    PREV="colegas_pre-M_\$(date -r 'colegas.sqlite' +%Y-%m-%d).sqlite"
    echo "  colegas.sqlite era un archivo regular -> se preserva como \$PREV"
    mv -n 'colegas.sqlite' "\$PREV"
fi
# swap atómico: se crea el link nuevo aparte y se lo mueve encima
ln -sfn '${BASENAME}' '.colegas.sqlite.nuevo'
mv -T '.colegas.sqlite.nuevo' 'colegas.sqlite'
echo "  colegas.sqlite -> \$(readlink colegas.sqlite)"
REMOTO

# ------------------------------------------------------ 6) rotación de uno
log "rotando (quedan la actual y la anterior)…"
ssh $SSH_OPTS "$VPS" "bash -s" <<'REMOTO'
set -euo pipefail
cd /srv/datasette
ACTUAL="$(readlink colegas.sqlite)"
# candidatos: todo .sqlite que no sea el symlink ni el destino vigente
mapfile -t VIEJOS < <(ls -1t *.sqlite 2>/dev/null | grep -v -x "$ACTUAL" || true)
if [ "${#VIEJOS[@]}" -le 1 ]; then
    echo "  nada para borrar (${#VIEJOS[@]} versión previa)"
else
    echo "  se conserva la anterior: ${VIEJOS[0]}"
    for f in "${VIEJOS[@]:1}"; do
        echo "  borrando versión vieja: $f"
        rm -f "$f"
    done
fi
REMOTO

# ------------------------------------------------------------- 7) reporte
log "verificación final…"
ssh $SSH_OPTS "$VPS" "ls -la ${REMOTE_DIR}/*.sqlite; echo; df -h ${REMOTE_DIR} | tail -1"

cat <<FIN

======================================================================
PUBLICADO
  época:   ${EPOCA}
  archivo: ${REMOTE_FILE}
  symlink: ${LINK} -> ${BASENAME}
  peso:    ${SIZE_MB} MB
  sha256:  ${SHA_LOCAL}   (idéntico en las dos puntas)
======================================================================
Los colegas verifican qué versión tienen con:
  SELECT * FROM _meta_version;
FIN
