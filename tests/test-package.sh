#!/usr/bin/env bash
# SPDX-License-Identifier: 0BSD

set -euo pipefail

readonly package_archive="${1:?usage: tests/test-package.sh PACKAGE.pkg.tar.zst}"
[[ -r "$package_archive" ]] || {
    printf 'cannot read package archive: %s\n' "$package_archive" >&2
    exit 1
}

pacman -Qip "$package_archive" >/dev/null

unexpected_paths="$({
    pacman -Qlp "$package_archive" \
        | sed 's|^[^ ]* ||' \
        | while IFS= read -r path; do
            case "$path" in
                /usr/|/usr/bin/|/usr/bin/chatgpt|/usr/lib/|/usr/lib/chatgpt|/usr/lib/chatgpt/*|\
                /usr/share/|/usr/share/applications/|/usr/share/applications/chatgpt.desktop|\
                /usr/share/pixmaps/|/usr/share/pixmaps/chatgpt.png|/usr/share/doc/|\
                /usr/share/doc/chatgpt-official-bin/|\
                /usr/share/doc/chatgpt-official-bin/third-party-notices)
                    ;;
                *)
                    printf '%s\n' "$path"
                    ;;
            esac
        done
} || true)"
[[ -z "$unexpected_paths" ]] || {
    printf 'unexpected package paths:\n%s\n' "$unexpected_paths" >&2
    exit 1
}

non_root_entries="$(
    bsdtar --numeric-owner -tvf "$package_archive" \
        | awk '$3 != 0 || $4 != 0 { count++ } END { print count + 0 }'
)"
[[ "$non_root_entries" -eq 0 ]] || {
    printf 'package contains %s entries not owned by root:root\n' "$non_root_entries" >&2
    exit 1
}

unsafe_mode_entries="$(
    bsdtar -tvf "$package_archive" \
        | awk '
            substr($1, 1, 1) != "l" &&
            (substr($1, 4, 1) ~ /[sS]/ ||
             substr($1, 7, 1) ~ /[sS]/ ||
             substr($1, 9, 1) == "w") { count++ }
            END { print count + 0 }
        '
)"
[[ "$unsafe_mode_entries" -eq 0 ]] || {
    printf 'package contains %s set-id or world-writable entries\n' "$unsafe_mode_entries" >&2
    exit 1
}

bsdtar -tvf "$package_archive" \
    | grep -Fq 'usr/bin/chatgpt -> ../lib/chatgpt/codex-launcher'

desktop_entry="$(bsdtar -xOf "$package_archive" usr/share/applications/chatgpt.desktop)"
grep -qx 'Exec=chatgpt %U' <<<"$desktop_entry"
grep -qx 'Icon=chatgpt' <<<"$desktop_entry"

bsdtar -xOf "$package_archive" \
    usr/share/doc/chatgpt-official-bin/third-party-notices \
    | grep -Fq 'Electron contributors'

printf 'package archive validation passed\n'
