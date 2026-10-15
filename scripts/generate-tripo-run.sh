#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export TEXT_ENCODER_DEVICE=cpu
export TEXT_ENCODER_MODE=local
export HF_HOME="${HF_HOME:-$PWD/.cache/huggingface}"
export HF_TOKEN_PATH="${HF_TOKEN_PATH:-/mnt/c/Users/SSAFY/.cache/huggingface/token}"
mkdir -p .cache/fresh-run docs/logs
start=$(date +%s)
set +e
/opt/deviant-kimodo/.venv/bin/kimodo_gen \
  'A person runs forward quickly and smoothly with a slight whole-body forward lean, clear alternating forward strides and backward push-offs, brief flight phases, natural opposing shoulder and pelvis rotation, relaxed hands swinging low around waist level below the chest, bent elbows swinging close to the sides, and a steady head looking forward' \
  --model Kimodo-SOMA-RP-v1.1 --duration 3.0 --num_samples 2 \
  --seed 107 --bvh --bvh_standard_tpose --output .cache/fresh-run/single \
  2>&1 | tee docs/logs/tripo-run-generation.log
result=${PIPESTATUS[0]}
set -e
echo "Exit status: $result; elapsed seconds: $(($(date +%s)-start))" | tee -a docs/logs/tripo-run-generation.log
exit "$result"
