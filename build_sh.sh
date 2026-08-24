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
src_dir="$script_dir/src"
entry_file="$src_dir/Account.dfy"
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
