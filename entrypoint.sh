#!/bin/sh
# Generate /usr/share/nginx/html/config.js from runtime env vars before nginx starts.
# Cloud Run injects env vars via --set-env-vars or --set-secrets.

set -e

CONFIG_PATH="/usr/share/nginx/html/config.js"

cat > "$CONFIG_PATH" <<EOF
window.READERLY_CONFIG = {
  AZURE_KEY: "${AZURE_KEY:-}",
  AZURE_REGION: "${AZURE_REGION:-eastus}",
  GEMINI_API_KEY: "${GEMINI_API_KEY:-}",
  GEMINI_MODEL: "${GEMINI_MODEL:-gemini-2.5-flash}"
};
EOF

# Fail loudly if a required key is missing — better than serving a broken app.
if [ -z "${AZURE_KEY:-}" ] || [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "FATAL: AZURE_KEY and GEMINI_API_KEY must be set at runtime." >&2
  exit 1
fi

exec nginx -g "daemon off;"
