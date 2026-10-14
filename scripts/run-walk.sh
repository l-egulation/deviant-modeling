#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
kimodo_env="${KIMODO_ENV:-/opt/deviant-kimodo/.venv}"
if [[ ! -x "$kimodo_env/bin/kimodo_gen" ]]; then
  echo 'Kimodo is missing. See docs/SETUP_RESULT.md for installation.' >&2
  exit 1
fi
export TEXT_ENCODER_DEVICE=cpu
export TEXT_ENCODER_MODE=local
export HF_HOME="${HF_HOME:-$PWD/.cache/huggingface}"
mkdir -p outputs docs/logs
"$kimodo_env/bin/python" scripts/check-gpu.py | tee docs/logs/gpu-check.json
"$kimodo_env/bin/python" scripts/check-model-access.py | tee docs/logs/model-access.log
start=$(date +%s)
set +e
"$kimodo_env/bin/kimodo_gen" \
  'A person walks forward at a relaxed pace with natural arm swing.' \
  --model Kimodo-SOMA-RP-v1.1 --duration 3.0 --num_samples 1 \
  --seed 42 --bvh --bvh_standard_tpose --output outputs/walk \
  2>&1 | tee docs/logs/walk-generation.log
result=${PIPESTATUS[0]}
set -e
echo "Exit status: $result; elapsed seconds (including model loading/download): $(($(date +%s)-start))" | tee -a docs/logs/walk-generation.log
if (( result != 0 )); then exit "$result"; fi
test -s outputs/walk.npz
test -s outputs/walk.bvh
