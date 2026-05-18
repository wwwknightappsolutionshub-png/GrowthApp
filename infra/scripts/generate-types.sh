#!/bin/bash
set -euo pipefail

# Generate TypeScript types from FastAPI OpenAPI schema

API_URL="${1:-http://localhost:8000}"
OUTPUT_DIR="$(dirname "$0")/../../packages/shared-types/src/generated"

echo "==> Fetching OpenAPI schema from ${API_URL}/openapi.json..."
mkdir -p "$OUTPUT_DIR"

npx openapi-typescript "${API_URL}/openapi.json" \
  --output "${OUTPUT_DIR}/api.d.ts"

echo "==> Types generated at ${OUTPUT_DIR}/api.d.ts"
