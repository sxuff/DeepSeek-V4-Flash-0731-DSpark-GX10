#!/usr/bin/env bash
set -euo pipefail

: "${DS4_RUNTIME_DIR:?set DS4_RUNTIME_DIR to the pinned Entrpi/ds4 checkout}"
: "${DS4_MODEL_PATH:?set DS4_MODEL_PATH to the exact normal 0731 target GGUF}"
: "${DS4_DRAFTER_PATH:?set DS4_DRAFTER_PATH to the exact 0731 Q2K/Q8 drafter GGUF}"

EXPECTED_RUNTIME=d183482b413ecd2e3b540b290e6497437e9fbb73
EXPECTED_MODEL_SHA=73b86c93e7b0be37f68c4b3a5361c7e17f9b278647aa335ea304ac5dfd784867
EXPECTED_DRAFTER_SHA=8fa269560dc76fd73e4233ad9b1938b5f65dd363381fd9b1a5c6183f7d12d686

[[ "$(git -C "$DS4_RUNTIME_DIR" rev-parse HEAD)" == "$EXPECTED_RUNTIME" ]]
[[ "$(sha256sum "$DS4_MODEL_PATH" | cut -d' ' -f1)" == "$EXPECTED_MODEL_SHA" ]]
[[ "$(sha256sum "$DS4_DRAFTER_PATH" | cut -d' ' -f1)" == "$EXPECTED_DRAFTER_SHA" ]]
[[ -x "$DS4_RUNTIME_DIR/ds4-server" ]]

export DS4_SERVER_COALESCE_MAX=2
export DS4_SERVER_DEFAULT_TEMP=0
export DS4_MEM_FLOOR_GB=16
export DS4_CONT_PREFILL_CHUNK=1024
export DS4_CONT_PREFILL_CHUNK_LIVE=1024
export DS4_NO_UPDATE_CHECK=1

mode=${1:-dspark}
case "$mode" in
  plain)
    spec=(--no-spec)
    ;;
  dspark)
    spec=(--dspark "$DS4_DRAFTER_PATH")
    export DS4_DSPARK_TRACE=1
    export DS4_DSPARK_PROFILE=1
    ;;
  *)
    printf 'usage: %s [plain|dspark]\n' "$0" >&2
    exit 2
    ;;
esac

exec "$DS4_RUNTIME_DIR/ds4-server" \
  -m "$DS4_MODEL_PATH" \
  "${spec[@]}" \
  --cuda --ctx 32768 --tokens 2048 \
  --mem-floor-gb 16 --host 127.0.0.1 --port 8001 \
  --no-update-check
