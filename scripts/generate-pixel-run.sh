#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export TEXT_ENCODER_DEVICE=cpu TEXT_ENCODER_MODE=local
export HF_HOME="$PWD/.cache/huggingface"
export HF_TOKEN_PATH=/mnt/c/Users/SSAFY/.cache/huggingface/token
mkdir -p .cache/pixel-run/generated docs/logs
/opt/deviant-kimodo/.venv/bin/kimodo_gen \
 'A person runs straight forward continuously at a steady fast pace, with natural alternating strides, a slight forward lean, relaxed bent elbows and low opposing arm swings, coordinated shoulder and hip rotation, and a steady head' \
 --model Kimodo-SOMA-RP-v1.1 --duration 3.0 --num_samples 2 --seed 231 \
 --bvh --bvh_standard_tpose --output .cache/pixel-run/generated \
 2>&1 | tee docs/logs/pixel-run-generation.log
