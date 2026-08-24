#!/bin/bash
# instalar_canal_descargas.sh — [FRENTE M] Canal de descarga de la base de colegas.
#
# Deja servido /descargas/ sobre el nginx que ya existe en el VPS, con contraseña.
# Idempotente: se puede correr las veces que haga falta.
#
# QUÉ HACE
#   1. Crea /srv/descargas con symlinks SÓLO a los artefactos publicados.
#      (No se sirve /srv/datasette: ahí vive datasette.env con el hash de la
#       clave del Datasette viejo.)
#   2. Escribe /etc/nginx/.htpasswd_colegas con la credencial.
#   3. Instala el snippet de nginx y lo incluye en el server{} de TLS.
#   4. Valida con `nginx -t` y recarga. Si la validación falla, RESTAURA el
#      backup y no recarga: el sitio no se queda roto.
#
# Uso:  scripts/ops/instalar_canal_descargas.sh <usuario> <password>
#
set -euo pipefail

VPS="root@187.124.150.28"
SSH_OPTS="-o ConnectTimeout=15 -o BatchMode=yes"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
SNIPPET_LOCAL="${REPO}/scripts/ops/nginx_descargas_colegas.conf"

USUARIO="${1:-}"
PASSWORD="${2:-}"

log() { echo "[$(date '+%F %T')] $*"; }
abort() { echo "[$(date '+%F %T')] ABORTA: $*" >&2; exit 1; }

[ -n "$USUARIO" ] && [ -n "$PASSWORD" ] || abort "uso: $0 <usuario> <password>"
[ -f "$SNIPPET_LOCAL" ] || abort "no está el snippet: $SNIPPET_LOCAL"

# El hash se calcula EN el VPS con openssl (htpasswd no está instalado y no
# vamos a instalar paquetes por esto). La contraseña viaja por el canal ssh,
# nunca queda en el disco local ni en el repo.
log "instalando canal de descargas…"
scp $SSH_OPTS "$SNIPPET_LOCAL" "${VPS}:/etc/nginx/snippets/descargas_colegas.conf"

ssh $SSH_OPTS "$VPS" "USUARIO='${USUARIO}' PASSWORD='${PASSWORD}' bash -s" <<'REMOTO'
set -euo pipefail
CONF=/etc/nginx/sites-enabled/datasette
SNIPPET=/etc/nginx/snippets/descargas_colegas.conf
BACKUP="/root/nginx_datasette.bak.$(date +%Y%m%d_%H%M%S)"

# --- 1) directorio de descargas con symlinks a lo publicado
mkdir -p /srv/descargas
find /srv/descargas -maxdepth 1 -type l -delete
for f in /srv/datasette/colegas_*.sqlite /srv/datasette/colegas_*.sqlite.gz /srv/datasette/colegas_*.sqlite.sha256; do
    [ -e "$f" ] || continue
    ln -sfn "$f" "/srv/descargas/$(basename "$f")"
done
echo "  /srv/descargas:"
ls -la /srv/descargas | tail -n +2 | sed 's/^/    /'

# --- 2) credencial (APR1 via openssl; htpasswd no está instalado)
HASH="$(openssl passwd -apr1 "$PASSWORD")"
printf '%s:%s\n' "$USUARIO" "$HASH" > /etc/nginx/.htpasswd_colegas
chmod 640 /etc/nginx/.htpasswd_colegas
chown root:www-data /etc/nginx/.htpasswd_colegas
echo "  credencial escrita para usuario '$USUARIO'"

# --- 3) incluir el snippet en el server{} de TLS (idempotente)
cp "$CONF" "$BACKUP"
echo "  backup: $BACKUP"

if grep -q 'descargas_colegas.conf' "$CONF"; then
    echo "  el include ya estaba: no se toca la config"
else
    python3 - "$CONF" <<'PY'
import re, sys
p = sys.argv[1]
txt = open(p).read()
# El server{} de TLS es el que escucha 443. Se inserta el include justo
# después de su primera línea server_name.
bloques = [m.start() for m in re.finditer(r'\bserver\s*\{', txt)]
destino = None
for i, ini in enumerate(bloques):
    fin = bloques[i+1] if i+1 < len(bloques) else len(txt)
    if 'listen 443' in txt[ini:fin]:
        destino = (ini, fin)
        break
if destino is None:
    raise SystemExit("no se encontró un server{} con listen 443")
ini, fin = destino
m = re.search(r'^\s*server_name[^;]*;\s*$', txt[ini:fin], re.M)
if not m:
    raise SystemExit("no se encontró server_name en el bloque TLS")
pos = ini + m.end()
txt = txt[:pos] + "\n\n    include /etc/nginx/snippets/descargas_colegas.conf;" + txt[pos:]
open(p, 'w').write(txt)
print("  include insertado en el server{} de TLS")
PY
fi

# --- 4) validar; si falla, restaurar y no recargar
if nginx -t 2>&1 | sed 's/^/    /'; then
    systemctl reload nginx
    echo "  ✓ nginx validado y recargado"
else
    cp "$BACKUP" "$CONF"
    rm -f "$SNIPPET"
    echo "  ✗ nginx -t FALLÓ — config restaurada desde el backup, sin recargar"
    exit 1
fi
REMOTO

log "listo. URL: https://187-124-150-28.sslip.io/descargas/"
