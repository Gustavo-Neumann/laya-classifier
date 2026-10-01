#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname -- "$SCRIPT_DIR")"
COMPOSE_FILE="$REPO_DIR/docker-compose.yml"

for command in docker uv; do
	if ! command -v "$command" >/dev/null 2>&1; then
		printf 'Required command not found: %s\n' "$command" >&2
		exit 1
	fi
done

export RABBITMQ_URL="${RABBITMQ_URL:-amqp://frclassifier:frclassifier_dev@localhost:5673/}"

docker compose -f "$COMPOSE_FILE" up --detach --wait rabbitmq

cd "$SCRIPT_DIR"
uv sync --frozen
exec uv run --no-sync laya-classifier-worker