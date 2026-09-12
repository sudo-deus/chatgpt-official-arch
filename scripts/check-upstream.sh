#!/usr/bin/env bash
# SPDX-License-Identifier: 0BSD

set -euo pipefail

readonly default_index_url='https://persistent.oaistatic.com/codex-app-prod/linux/deb/dists/stable/main/binary-amd64/Packages'
readonly index_url="${CHATGPT_PACKAGES_URL:-$default_index_url}"
readonly package_file="${PKGBUILD_PATH:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)/PKGBUILD}"

die() {
    printf 'check-upstream: %s\n' "$*" >&2
    exit 1
}

[[ -r "$package_file" ]] || die "cannot read PKGBUILD: $package_file"

index_tmp="$(mktemp)"
trap 'rm -f "$index_tmp"' EXIT

if [[ -n "${CHATGPT_PACKAGES_FILE:-}" ]]; then
    [[ -r "$CHATGPT_PACKAGES_FILE" ]] || die "cannot read package index: $CHATGPT_PACKAGES_FILE"
    cp -- "$CHATGPT_PACKAGES_FILE" "$index_tmp"
else
    curl --fail --silent --show-error --location \
        --proto '=https' --tlsv1.2 \
        "$index_url" -o "$index_tmp"
fi

mapfile -t stanza < <(
    awk '
        BEGIN { RS=""; FS="\n" }
        {
            package=""; version=""; architecture=""; filename=""; sha256=""
            for (i = 1; i <= NF; i++) {
                if ($i ~ /^Package: /) package=substr($i, 10)
                else if ($i ~ /^Version: /) version=substr($i, 10)
                else if ($i ~ /^Architecture: /) architecture=substr($i, 15)
                else if ($i ~ /^Filename: /) filename=substr($i, 11)
                else if ($i ~ /^SHA256: /) sha256=substr($i, 9)
            }
            if (package == "chatgpt" && architecture == "amd64")
                print version "\t" architecture "\t" filename "\t" sha256
        }
    ' "$index_tmp"
)

[[ "${#stanza[@]}" -eq 1 ]] || die "expected exactly one chatgpt/amd64 stanza; found ${#stanza[@]}"

IFS=$'\t' read -r upstream_version upstream_arch upstream_filename upstream_sha256 <<<"${stanza[0]}"

[[ "$upstream_version" =~ ^[0-9]+([.][0-9]+)+$ ]] || die "invalid upstream version: $upstream_version"
[[ "$upstream_arch" == 'amd64' ]] || die "invalid upstream architecture: $upstream_arch"
[[ "$upstream_sha256" =~ ^[0-9a-f]{64}$ ]] || die "invalid upstream SHA-256: $upstream_sha256"

expected_filename="pool/main/c/chatgpt/chatgpt_${upstream_version}_amd64.deb"
[[ "$upstream_filename" == "$expected_filename" ]] || die "unexpected upstream filename: $upstream_filename"

packaged_version="$(sed -n 's/^pkgver=//p' "$package_file")"
packaged_sha256="$(sed -n "/^sha256sums_x86_64=(/,/^)/s/^[[:space:]]*'\([0-9a-f]\{64\}\)'[[:space:]]*$/\1/p" "$package_file")"

[[ "$packaged_version" =~ ^[0-9]+([.][0-9]+)+$ ]] || die 'unable to read a valid pkgver from PKGBUILD'
[[ "$packaged_sha256" =~ ^[0-9a-f]{64}$ ]] || die 'unable to read exactly one x86-64 SHA-256 from PKGBUILD'

status='current'
exit_code=0
if [[ "$packaged_version" != "$upstream_version" || "$packaged_sha256" != "$upstream_sha256" ]]; then
    status='outdated'
    exit_code=10
fi

printf 'status=%s\n' "$status"
printf 'packaged_version=%s\n' "$packaged_version"
printf 'upstream_version=%s\n' "$upstream_version"
printf 'upstream_filename=%s\n' "$upstream_filename"
printf 'upstream_sha256=%s\n' "$upstream_sha256"

exit "$exit_code"
