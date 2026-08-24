#!/usr/bin/env bash
#
# Usage:
#     ./build.sh
#     ./build.sh py
#     ./build.sh cs
#
# Dafny target examples:
#     - cs  = C#
#     - py  = Python
#     - js  = JavaScript
#

if [[ $# -gt 1 ]]; then
  echo "Usage: $0 [target]" >&2
  echo "Default target: py" >&2
  exit 1
fi

compile_target="${1:-py}"

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
src_dir="$script_dir/dafny"
entry_file="$src_dir/Account.dfy"

if ! command -v dafny >/dev/null 2>&1; then
  echo 'Dafny is required. Install Dafny and ensure "dafny" is on PATH.' >&2
  exit 1
fi

if [[ ! -f "$entry_file" ]]; then
  echo "Dafny entry file not found: $entry_file" >&2
  exit 1
fi
case "$compile_target" in
  js)
    build_dir="$script_dir/typescript"
    output_dir="$build_dir/compiled"
    output_file="$output_dir/VQC.js"
    ;;
  py)
    build_dir="$script_dir"
    output_dir="$script_dir/python/compiled"
    output_file="$output_dir/VQC.py"
    ;;
  *)
    build_dir="$script_dir"
    output_root="$script_dir/compiled"
    output_dir="$output_root/$compile_target"
    output_file="$output_dir/VQC.$compile_target"
    ;;
esac

if [[ "$compile_target" == "py" ]]; then
  python_bin="$script_dir/python/.venv/bin/python"
  if [[ ! -x "$python_bin" ]]; then
    echo 'Python virtual environment not found. Create python/.venv and install python/requirements.txt.' >&2
    exit 1
  fi

  if ! "$python_bin" -c 'import alpaca, dotenv, schedule'; then
    echo 'Python dependencies are missing. Run python/.venv/bin/python -m pip install -r python/requirements.txt.' >&2
    exit 1
  fi
fi

if [[ "$compile_target" == "js" ]]; then
  if ! command -v node >/dev/null 2>&1; then
    echo 'Node.js is required for the JavaScript target. Install Node.js and ensure "node" is on PATH.' >&2
    exit 1
  fi

  if [[ ! -f "$script_dir/typescript/node_modules/bignumber.js/package.json" ]]; then
    echo 'TypeScript dependency bignumber.js is missing. Run "cd typescript && npm install".' >&2
    exit 1
  fi

  if [[ ! -x "$script_dir/typescript/node_modules/.bin/tsc" ]] && ! command -v tsc >/dev/null 2>&1; then
    echo 'TypeScript compiler is missing. Install TypeScript globally or add it locally with npm.' >&2
    exit 1
  fi
fi

if [[ -d "$output_dir" ]]; then
  rm -rf "$output_dir"
fi

mkdir -p "$output_dir"

(
  cd "$build_dir"
  dafny build "$entry_file" --target:"$compile_target" --output:"$output_file"
  if [[ "$compile_target" == "js" ]]; then
    printf '\nmodule.exports = { BigNumber, _dafny, Types, Validation, Currency, Orders, AccountOps };\n' >> "$output_file"
  fi
)
