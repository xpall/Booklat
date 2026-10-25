#!/usr/bin/env bash
# Booklat watchdog: restarts the web container if the app stops responding.
#
# Intended to run from cron every minute:
#   * * * * * /path/to/booklat/scripts/watchdog.sh >/dev/null 2>&1
#
# Requires permission to run `docker` (root, or a user in the docker group).
# Tunables (env or edit defaults):
#   APP_PORT            host port from .env      (default 8010)
#   WATCHDOG_URL        URL to probe             (default http://127.0.0.1:<APP_PORT>/accounts/login/)
#   WATCHDOG_FAILS      consecutive failures     (default 3)
#   WATCHDOG_STATE      state file               (default /var/tmp/booklat-watchdog.fails)
#   WATCHDOG_CONTAINER  container to restart     (default booklat-web)
#   BOOKLAT_ENV_FILE    path to .env             (default ../.env next to this script)

set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ENV_FILE="${BOOKLAT_ENV_FILE:-$SCRIPT_DIR/../.env}"

if [ -z "${APP_PORT:-}" ] && [ -f "$ENV_FILE" ]; then
    APP_PORT="$(
        sed -n 's/^[[:space:]]*APP_PORT[[:space:]]*=[[:space:]]*//p' "$ENV_FILE" \
            | tail -n 1 \
            | tr -d '\r' \
            | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' \
                  -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//"
    )"
fi

APP_PORT="${APP_PORT:-8010}"
case "$APP_PORT" in
    *[!0-9]*) APP_PORT=8010 ;;
esac

URL="${WATCHDOG_URL:-http://127.0.0.1:${APP_PORT}/accounts/login/}"
FAILS="${WATCHDOG_FAILS:-3}"
STATE="${WATCHDOG_STATE:-/var/tmp/booklat-watchdog.fails}"
CONTAINER="${WATCHDOG_CONTAINER:-booklat-web}"

if [ "$(id -u)" = "0" ]; then
    docker_cmd() { docker "$@"; }
else
    docker_cmd() { sudo docker "$@"; }
fi

code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 10 "$URL" || echo 000)"

if [ "$code" = "200" ] || [ "$code" = "302" ]; then
    echo 0 > "$STATE" 2>/dev/null || true
    exit 0
fi

n="$(cat "$STATE" 2>/dev/null || echo 0)"
case "$n" in ''|*[!0-9]*) n=0 ;; esac
n=$((n + 1))
echo "$n" > "$STATE" 2>/dev/null || true
logger -t booklat-watchdog "probe failed code=$code consecutive=$n" 2>/dev/null || true

if [ "$n" -ge "$FAILS" ]; then
    logger -t booklat-watchdog "restarting $CONTAINER" 2>/dev/null || true
    docker_cmd restart "$CONTAINER"
    echo 0 > "$STATE" 2>/dev/null || true
fi
