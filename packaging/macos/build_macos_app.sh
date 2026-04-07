#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PACKAGING_DIR="${ROOT_DIR}/packaging/macos"
PYTHON_BIN="${PYTHON_BIN:-}"
LOCAL_FRAMEWORK_ROOT="${ROOT_DIR}/.tools/python312"
LOCAL_PYTHON_BIN="${LOCAL_FRAMEWORK_ROOT}/Python.framework/Versions/3.12/bin/python3.12"
export PYINSTALLER_CONFIG_DIR="${ROOT_DIR}/.tools/pyinstaller"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "This build script only supports macOS." >&2
  exit 1
fi

if [[ -z "${PYTHON_BIN}" ]]; then
  if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3.12)"
  elif [[ -x "/opt/homebrew/bin/python3.12" ]]; then
    PYTHON_BIN="/opt/homebrew/bin/python3.12"
  elif [[ -x "${LOCAL_PYTHON_BIN}" ]]; then
    PYTHON_BIN="${LOCAL_PYTHON_BIN}"
    export DYLD_FRAMEWORK_PATH="${LOCAL_FRAMEWORK_ROOT}"
    export DYLD_LIBRARY_PATH="${LOCAL_FRAMEWORK_ROOT}/Python.framework/Versions/3.12/lib"
    export PYTHONHOME="${LOCAL_FRAMEWORK_ROOT}/Python.framework/Versions/3.12"
  else
    echo "python3.12 was not found. Install it first with: brew install python@3.12" >&2
    echo "Alternatively, place a local Python.framework at .tools/python312/Python.framework" >&2
    exit 1
  fi
fi

for tool in iconutil sips; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    echo "Missing required macOS tool: ${tool}" >&2
    exit 1
  fi
done

if [[ "$(uname -m)" != "arm64" ]]; then
  echo "This build is configured for Apple Silicon (arm64) only." >&2
  exit 1
fi

cd "${ROOT_DIR}"
mkdir -p "${PYINSTALLER_CONFIG_DIR}"

if [[ -x ".venv/bin/python" ]]; then
  EXISTING_VENV_VERSION="$("./.venv/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  if [[ "${EXISTING_VENV_VERSION}" != "3.12" ]]; then
    echo "Existing .venv uses Python ${EXISTING_VENV_VERSION}. Remove .venv or set PYTHON_BIN to a Python 3.12 interpreter." >&2
    exit 1
  fi
else
  "${PYTHON_BIN}" -m venv .venv
fi

VENV_PYTHON="${ROOT_DIR}/.venv/bin/python"
VENV_PIP="${ROOT_DIR}/.venv/bin/pip"
VENV_PYTEST="${ROOT_DIR}/.venv/bin/pytest"
VENV_PYINSTALLER="${ROOT_DIR}/.venv/bin/pyinstaller"

"${VENV_PIP}" install --upgrade pip setuptools wheel
"${VENV_PIP}" install -r requirements.txt -r requirements-build.txt
"${VENV_PYTHON}" "${PACKAGING_DIR}/patch_pyinstaller_compat.py"
"${VENV_PYTEST}" -q
"${VENV_PYTHON}" "${PACKAGING_DIR}/generate_icon.py"

MASTER_ICON_PATH="${PACKAGING_DIR}/assets/srt_to_xml.png"
ICONSET_DIR="${PACKAGING_DIR}/assets/srt_to_xml.iconset"
ICNS_PATH="${PACKAGING_DIR}/assets/srt_to_xml.icns"

mkdir -p "${ICONSET_DIR}"

for size in 16 32 128 256 512; do
  sips -z "${size}" "${size}" "${MASTER_ICON_PATH}" --out "${ICONSET_DIR}/icon_${size}x${size}.png" >/dev/null
  double_size=$((size * 2))
  sips -z "${double_size}" "${double_size}" "${MASTER_ICON_PATH}" --out "${ICONSET_DIR}/icon_${size}x${size}@2x.png" >/dev/null
done

iconutil -c icns "${ICONSET_DIR}" -o "${ICNS_PATH}"
"${VENV_PYINSTALLER}" "${PACKAGING_DIR}/srt_to_xml.spec" --noconfirm --clean

echo "Built app: ${ROOT_DIR}/dist/srt_to_xml.app"
