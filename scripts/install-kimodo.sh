#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
# Run in the existing Ubuntu-22.04 WSL distribution as root (or with sudo).
if (( EUID != 0 )); then echo 'Run with sudo for system dependencies.' >&2; exit 1; fi
mkdir -p docs/logs
exec > >(tee docs/logs/install-kimodo.log) 2>&1
date -Is
apt-get update
apt-get install -y python3.10-venv python3.10-dev cmake build-essential git
kimodo_env="${KIMODO_ENV:-/opt/deviant-kimodo/.venv}"
python3.10 -m venv "$kimodo_env"
"$kimodo_env/bin/python" -m pip install --upgrade pip
"$kimodo_env/bin/python" -m pip install 'torch==2.11.0' --index-url https://download.pytorch.org/whl/cu128
"$kimodo_env/bin/python" -m pip install \
  'kimodo[all] @ git+https://github.com/nv-tlabs/kimodo.git@58e781898b3d7e328a676a75d3e338c45dce3ad9'
"$kimodo_env/bin/python" scripts/check-gpu.py
