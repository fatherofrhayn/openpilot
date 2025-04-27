#!/usr/bin/env bash
set -e

# Bootstrap development environment for openpilot

# Create virtual environment if missing
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# Define venv tools
VENV_PYTHON=".venv/bin/python3"
VENV_PIP="$VENV_PYTHON -m pip"
# Use the venv scons executable directly
VENV_SCONS=".venv/bin/scons"

# Install dependencies into venv
$VENV_PIP install --upgrade pip
$VENV_PIP install -r requirements.txt
$VENV_PIP install -e fork_manager

export PATH="$(pwd)/.venv/bin:$PATH"

echo "Development environment ready; starting build..."

# Run build with venv scons
"$VENV_PYTHON" -m SCons -c
"$VENV_PYTHON" -m SCons
./selfdrive/ui/ui
