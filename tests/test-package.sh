#!/usr/bin/env bash
# SPDX-License-Identifier: 0BSD
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
archive="${1:?usage: tests/test-package.sh PACKAGE.pkg.tar.zst}"
pacman -Qip "$archive" >/dev/null
args=()
if [[ -n "${2:-}" ]]; then
    args=(--upstream-tree "$2")
fi
python3 "$root/upstream.py" package "$archive" "${args[@]}"
