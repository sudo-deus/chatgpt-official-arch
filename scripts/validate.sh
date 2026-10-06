#!/usr/bin/env bash
# SPDX-License-Identifier: 0BSD
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
bash -n PKGBUILD scripts/*.sh tests/*.sh
tests/test-check-upstream.sh
python3 upstream.py local-sources
srcinfo="$(mktemp)"
trap 'rm -f "$srcinfo"' EXIT
makepkg --printsrcinfo > "$srcinfo"
diff -u .SRCINFO "$srcinfo"
# Verifies helpers as well as upstream when --full is requested.
if [[ "${1:-}" == '--full' ]]; then
    makepkg --verifysource --force
    makepkg --cleanbuild --force
    mapfile -t packages < <(makepkg --packagelist)
    [[ "${#packages[@]}" -eq 1 ]]
    tests/test-package.sh "${packages[0]}" src/deb-unpack/data
    namcap -m PKGBUILD > namcap-recipe.log 2>&1
    namcap -m "${packages[0]}" > namcap-package.log 2>&1
    cat namcap-recipe.log namcap-package.log
    python3 scripts/check-namcap.py namcap-recipe.log namcap-package.log
fi
