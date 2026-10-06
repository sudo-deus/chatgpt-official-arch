#!/usr/bin/env bash
# SPDX-License-Identifier: 0BSD
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$root/upstream.py" check "$@"
