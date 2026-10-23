#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export TEXT_ENCODER_DEVICE=cpu TEXT_ENCODER_MODE=local
export HF_HOME="$PWD/.cache/huggingface"
export HF_TOKEN_PATH=/mnt/c/Users/SSAFY/.cache/huggingface/token
mkdir -p .cache/pixel-run/generated docs/logs
/opt/deviant-kimodo/.venv/bin/kimodo_gen \
 'A person runs naturally at a comfortable medium speed with a straight aligned spine and head held upright looking straight ahead, the whole body inclines slightly forward from the ankles, relaxed bent elbows swing back and forth alongside the torso, smooth alternating strides with steady balanced running posture' \
 --model Kimodo-SOMA-RP-v1.1 --duration 3.0 --num_samples 4 --seed 983 \
 --bvh --bvh_standard_tpose --output .cache/pixel-run/generated \
 2>&1 | tee docs/logs/pixel-run-generation.log
