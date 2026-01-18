#!/bin/bash
# VFX Ingest Platform - Docker Installation Bootstrap
# Wrapper script to run the Docker installation wizard

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

python3 scripts/install_wizard.py --docker "$@"
