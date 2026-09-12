#!/usr/bin/env bash
# SPDX-License-Identifier: 0BSD

set -euo pipefail

readonly root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
readonly checker="$root/scripts/check-upstream.sh"

current_output="$(CHATGPT_PACKAGES_FILE="$root/tests/fixtures/Packages.current" "$checker")"
grep -qx 'status=current' <<<"$current_output"
grep -qx 'upstream_version=26.908.40834' <<<"$current_output"

set +e
newer_output="$(CHATGPT_PACKAGES_FILE="$root/tests/fixtures/Packages.newer" "$checker" 2>&1)"
newer_status=$?
set -e

[[ "$newer_status" -eq 10 ]]
grep -qx 'status=outdated' <<<"$newer_output"
grep -qx 'upstream_version=26.909.10000' <<<"$newer_output"

printf 'check-upstream tests passed\n'
