#!/usr/bin/env bash
# Booklat hang diagnostics. READ-ONLY. Writes one log file and prints it.
#
# Usage:
#   sudo bash scripts/diagnose-hang.sh              # recommended
#   sudo bash scripts/diagnose-hang.sh /tmp/out.log
#
# Every command is wrapped in `timeout` so this script cannot hang.

set -u
export LANG=C

TS="$(date +%Y%m%d-%H%M%S)"
OUT="${1:-/var/tmp/booklat-hang-$TS.log}"

if [ "$(id -u)" = "0" ]; then
    DOCKER=(docker)
else
    DOCKER=(sudo docker)
fi

WEB=booklat-web
DB=booklat-db
REDIS=booklat-redis
CELERY_W=booklat-celery-worker
BEAT=booklat-celery-beat

section() { printf '\n========== %s ==========\n' "$1"; }
note()    { printf '  (skipped/failed: %s)\n' "$1"; }

main() {
    section "BOOKLAT HANG DIAGNOSTICS"
    echo "timestamp : $(date -Is)"
    echo "hostname  : $(hostname)  user=$(id -un) uid=$(id -u)"
    echo "output    : $OUT"
    echo "uptime    : $(uptime)"

    section "CONTAINER STATE"
    timeout 20 "${DOCKER[@]}" ps -a 2>&1 || note "docker ps"
    for c in "$WEB" "$DB" "$REDIS" "$CELERY_W" "$BEAT"; do
        echo "--- $c"
        timeout 15 "${DOCKER[@]}" inspect -f \
            'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} restarts={{.RestartCount}} started={{.State.StartedAt}} logdriver={{.HostConfig.LogConfig.Type}} logopts={{.HostConfig.LogConfig.Config}}' \
            "$c" 2>&1 || note "inspect $c"
    done

    section "HOST RESOURCES"
    nproc 2>&1
    uptime 2>&1
    free -m 2>&1
    df -h 2>&1
    echo "--- vmstat 1 5"
    timeout 15 vmstat 1 5 2>&1 || note "vmstat"
    echo "--- dmesg tail"
    { dmesg -T 2>/dev/null || sudo dmesg -T 2>/dev/null || true; } | tail -40

    section "PORT :8000 STATE (worker exhaustion?)"
    timeout 15 ss -tnp 2>&1 | grep ':8000' | head -60 || note "ss"
    echo "--- connection state counts"
    timeout 15 ss -tan 2>&1 | awk 'NR>1{print $1}' | sort | uniq -c || note "ss counts"

    section "HTTP PROBES (root, login, static)"
    for url in \
        "http://localhost:8000/" \
        "http://localhost:8000/accounts/login/" \
        "http://localhost:8000/static/core/css/design-system.css"; do
        echo "--- $url"
        timeout 20 curl -sS -o /dev/null \
            -w 'http=%{http_code} connect=%{time_connect}s ttfb=%{time_starttransfer}s total=%{time_total}s\n' \
            --connect-timeout 5 --max-time 15 "$url" 2>&1 || note "curl $url timed out"
    done

    section "WEB PROCESS / THREAD TREE"
    echo "--- docker top $WEB (host PIDs)"
    timeout 15 "${DOCKER[@]}" top "$WEB" 2>&1 || note "docker top"
    echo "--- docker exec ps -eLf"
    timeout 15 "${DOCKER[@]}" exec "$WEB" sh -c 'ps -eLf 2>/dev/null || ls /proc | grep -E "^[0-9]+$"' 2>&1 || note "ps/proc"

    section "PYTHON STACK TRACES (py-spy, SYS_PTRACE one-off container)"
    # Docker's default seccomp blocks ptrace inside the app container, so run
    # py-spy from a throwaway container sharing the web container's PID namespace.
    timeout 180 "${DOCKER[@]}" run --rm \
        --pid="container:$WEB" \
        --cap-add SYS_PTRACE \
        --security-opt seccomp=unconfined \
        python:3.12-slim sh -c '
            pip install -q py-spy >/dev/null 2>&1 || { echo "py-spy install failed"; exit 0; }
            for d in /proc/[0-9]*; do
                p=${d#/proc/}
                c=$(tr "\0" " " < "$d/cmdline" 2>/dev/null)
                case "$c" in
                    *gunicorn*) echo "===== PID $p : $c"; py-spy dump --nonblocking --pid "$p" 2>&1 ;;
                esac
            done
        ' 2>&1 || note "py-spy capture (needs internet to pull python:3.12-slim)"

    section "POSTGRES"
    PSQL_QUERIES=(
        "select version();"
        "show max_connections;"
        "select count(*) as connections from pg_stat_activity;"
        "select pg_size_pretty(pg_database_size(current_database())) as db_size;"
        "select count(*) as session_rows from django_session;"
        "select pid, usename, state, wait_event_type, wait_event, now()-xact_start as xact_age, now()-query_start as query_age, left(query,120) as query from pg_stat_activity where pid<>pg_backend_pid() order by xact_start nulls last;"
        "select blocked.pid as blocked_pid, blocking.pid as blocking_pid from pg_stat_activity blocked join pg_stat_activity blocking on blocking.pid=any(pg_blocking_pids(blocked.pid));"
        "select count(*), state from pg_stat_activity group by state;"
        "select relname, n_live_tup from pg_stat_user_tables order by n_live_tup desc limit 10;"
    )
    for q in "${PSQL_QUERIES[@]}"; do
        echo "--- $q"
        timeout 20 "${DOCKER[@]}" exec "$DB" psql -U booklat -d booklat -P pager=off -c "$q" 2>&1 || note "psql timeout"
    done

    section "REDIS"
    echo "--- PING"
    timeout 15 "${DOCKER[@]}" exec "$REDIS" redis-cli ping 2>&1 || note "redis ping"
    echo "--- INFO"
    timeout 15 "${DOCKER[@]}" exec "$REDIS" redis-cli INFO 2>&1 || note "redis INFO"
    echo "--- CLIENT LIST"
    timeout 15 "${DOCKER[@]}" exec "$REDIS" redis-cli CLIENT LIST 2>&1 || note "redis CLIENT LIST"
    echo "--- SLOWLOG GET 20"
    timeout 15 "${DOCKER[@]}" exec "$REDIS" redis-cli SLOWLOG GET 20 2>&1 || note "redis SLOWLOG"
    echo "--- latency sample (8s)"
    timeout 8 "${DOCKER[@]}" exec "$REDIS" redis-cli --latency 2>&1 | head -n 20 || note "redis latency"

    section "CELERY"
    echo "--- worker inspect active"
    timeout 25 "${DOCKER[@]}" exec "$CELERY_W" celery -A config inspect active 2>&1 | head -60 || note "celery inspect active"
    echo "--- worker inspect reserved"
    timeout 25 "${DOCKER[@]}" exec "$CELERY_W" celery -A config inspect reserved 2>&1 | head -60 || note "celery inspect reserved"
    echo "--- worker log tail"
    timeout 20 "${DOCKER[@]}" logs --tail 100 "$CELERY_W" 2>&1 || note "celery worker logs"
    echo "--- beat log tail"
    timeout 20 "${DOCKER[@]}" logs --tail 60 "$BEAT" 2>&1 || note "celery beat logs"

    section "WEB LOG (full tail)"
    timeout 20 "${DOCKER[@]}" logs --tail 200 "$WEB" 2>&1 || note "web logs"

    section "WEB LOG (errors/timeouts only)"
    timeout 20 "${DOCKER[@]}" logs --tail 1000 "$WEB" 2>&1 \
        | grep -iE 'timeout|error|critical|traceback|exception|refused|reset' | tail -100 || note "no matching log lines"

    section "DOCKER LOG FILE SIZES"
    timeout 20 du -sh /var/lib/docker/containers/*/*-json.log 2>/dev/null | sort -h | tail -20 || note "du log sizes"

    section "END"
    echo "done at $(date -Is)"
}

main 2>&1 | tee "$OUT"
echo
echo "============================================================"
echo "Log written to: $OUT"
echo "Send me that file's contents."
echo "============================================================"
