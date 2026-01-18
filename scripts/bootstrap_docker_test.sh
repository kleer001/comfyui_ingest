#!/bin/bash
# VFX Ingest Platform - Docker Installation Bootstrap (with tests)
# Wrapper script to run the Docker installation wizard with test pipeline

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

python3 scripts/install_wizard.py --docker --test "$@"
