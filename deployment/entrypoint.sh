#!/bin/sh
set -eu

echo "=> entrypoint.sh: starting"

# Config
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
MAX_RETRIES="${MAX_RETRIES:-30}"
SLEEP_INTERVAL="${SLEEP_INTERVAL:-2}"

wait_for_postgres() {
  if command -v pg_isready >/dev/null 2>&1; then
    echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT}..."
    n=0
    until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
      n=$((n+1))
      if [ "$n" -ge "$MAX_RETRIES" ]; then
        echo "Postgres not ready after $n attempts."
        return 1
      fi
      echo "Postgres unavailable - sleeping ${SLEEP_INTERVAL}s (attempt: $n/${MAX_RETRIES})"
      sleep "$SLEEP_INTERVAL"
    done
    echo "Postgres is ready."
  else
    echo "pg_isready not found - skipping explicit Postgres wait."
  fi
}

run_with_retries() {
  cmd="$1"
  n=0
  while true; do
    if sh -c "$cmd"; then
      break
    fi
    n=$((n+1))
    if [ "$n" -ge "$MAX_RETRIES" ]; then
      echo "Command failed after $n attempts: $cmd"
      return 1
    fi
    echo "Command failed, retrying in ${SLEEP_INTERVAL}s (attempt: $n/${MAX_RETRIES})"
    sleep "$SLEEP_INTERVAL"
  done
  return 0
}

# --- main flow ---
if ! wait_for_postgres; then
  echo "Warning: Postgres didn't become ready in time. We'll still try migrations (which may fail)."
fi

echo "Running migrations..."
if ! run_with_retries "python manage.py migrate --noinput"; then
  echo "ERROR: Migrations failed after all retries"
  exit 1
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Warning: collectstatic failed, continuing anyway"

# Optional: create superuser if env vars supplied
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  echo "Ensuring superuser ${DJANGO_SUPERUSER_USERNAME} exists..."
  python - <<PY
from django.contrib.auth import get_user_model
User = get_user_model()
username = "${DJANGO_SUPERUSER_USERNAME}"
email = "${DJANGO_SUPERUSER_EMAIL}"
password = "${DJANGO_SUPERUSER_PASSWORD}"
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("Superuser created.")
else:
    print("Superuser already exists.")
PY
fi

# Show the command being executed
if [ "$#" -eq 0 ]; then
  echo "=> entrypoint.sh: finished setup — no command provided."
else
  printf '=> entrypoint.sh: finished setup — executing:'
  for arg in "$@"; do
    printf ' %s' "$arg"
  done
  printf '\n'
fi

# Replace shell with the requested command so signals are forwarded
exec "$@"