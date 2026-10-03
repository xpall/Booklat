#!/usr/bin/env bash
# Booklat watchdog: restarts the web container if the app stops responding.
#
# Intended to run from cron every minute:
#   * * * * * /path/to/booklat/scripts/watchdog.sh >/dev/null 2>&1
#
# Requires permission to run `docker` (root, or a user in the docker group).
# Tunables (env or edit defaults):
#   WATCHDOG_URL        URL to probe            (default http://127.0.0.1:8000/accounts/login/)
#   WATCHDOG_FAILS      consecutive failures    (default 3)
#   WATCHDOG_STATE      state file              (default /var/tmp/booklat-watchdog.fails)
#   WATCHDOG_CONTAINER  container to restart    (default booklat-web)

set -u

URL="${WATCHDOG_URL:-http://127.0.0.1:8000/accounts/login/}"
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
