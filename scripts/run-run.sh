#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
kimodo_env="${KIMODO_ENV:-/opt/deviant-kimodo/.venv}"
export TEXT_ENCODER_DEVICE=cpu
export TEXT_ENCODER_MODE=local
export HF_HOME="${HF_HOME:-$PWD/.cache/huggingface}"
mkdir -p .cache/run-candidates docs/logs
start=$(date +%s)
set +e
"$kimodo_env/bin/kimodo_gen" \
  'A person runs forward at a steady brisk pace with a slight forward lean and natural alternating arm swings.' \
  --model Kimodo-SOMA-RP-v1.1 --duration 3.0 --num_samples 2 \
  --seed 46 --bvh --bvh_standard_tpose --output .cache/run-candidates/run \
  2>&1 | tee docs/logs/run-generation.log
result=${PIPESTATUS[0]}
set -e
echo "Exit status: $result; elapsed seconds (including model loading): $(($(date +%s)-start))" | tee -a docs/logs/run-generation.log
exit "$result"
