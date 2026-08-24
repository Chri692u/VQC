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
output_root="$script_dir/compiled"
output_dir="$output_root/$compile_target"
output_file="$output_dir/VQC.$compile_target"

if [[ -d "$output_dir" ]]; then
  rm -rf "$output_dir"
fi

mkdir -p "$output_dir"

dafny build "$entry_file" --target:"$compile_target" --output:"$output_file"