#!/usr/bin/env bash
set -euo pipefail

bash -n scripts/*.sh
python3 -m compileall -q scripts tests
python3 -m unittest discover -s tests -v
python3 scripts/verify_repo.py

echo REPOSITORY_CHECKS_OK
