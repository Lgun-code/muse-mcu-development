#!/usr/bin/env bash
# bootstrap.sh - deploy the Muse cloud toolchain for STM32 development.
#
# Idempotent: safe to re-run. Installs PlatformIO Core into a dedicated
# virtualenv at ~/.venvs/pio (never into the system Python). The ARM GCC
# toolchain, the ST platform and the STM32Cube framework packages are NOT
# installed here; PlatformIO downloads them automatically on the first
# `pio run` inside a project (expect several hundred MB and a few minutes).
#
# Validated on Ubuntu 24.04, Python 3.12.3, PlatformIO Core 6.2.0.
#
# Usage:
#   bash bootstrap.sh                # install or verify the toolchain
#   bash bootstrap.sh --check-only   # report status, install nothing
set -euo pipefail

VENV_DIR="$HOME/.venvs/pio"
PIO="$VENV_DIR/bin/pio"
CHECK_ONLY=0
[ "${1:-}" = "--check-only" ] && CHECK_ONLY=1

echo "== Host =="
uname -a || true
python3 --version || { echo "FAIL: python3 not found"; exit 1; }
gcc --version | head -1 || true

if [ -x "$PIO" ]; then
  echo "== PlatformIO already installed =="
  "$PIO" --version
  echo "BOOTSTRAP OK"
  exit 0
fi

if [ "$CHECK_ONLY" = "1" ]; then
  echo "PlatformIO not installed at $VENV_DIR (run without --check-only to install)"
  exit 2
fi

echo "== Installing PlatformIO into $VENV_DIR =="
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install platformio
"$PIO" --version

echo ""
echo "Add to PATH for this shell with:"
echo "  export PATH=\"\$HOME/.venvs/pio/bin:\$PATH\""
echo "First 'pio run' in a project downloads platform ststm32, the"
echo "STM32Cube framework package and toolchain-gccarmnoneeabi."
echo "BOOTSTRAP OK"
