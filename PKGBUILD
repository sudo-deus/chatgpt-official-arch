# SPDX-License-Identifier: 0BSD

pkgname=chatgpt-official-bin
pkgver=26.908.40834
pkgrel=1
pkgdesc="Official ChatGPT desktop app for Linux, repackaged for Arch/Artix"
arch=('x86_64')
url='https://developers.openai.com/codex/app'
# OpenAI does not ship a license for the proprietary ChatGPT application.
# The Debian copyright file currently contains third-party Electron notices only.
license=('unknown')

provides=("chatgpt=${pkgver}")
conflicts=('chatgpt')

depends=(
    'alsa-lib'
    'at-spi2-core'
    'cairo'
    'dbus'
    'expat'
    'gdk-pixbuf2'
    'glib2'
    'glibc'
    'gtk3'
    'libcups'
    'libdrm'
    'libgcc'
    'libglvnd'          # Debian libgl1
    'libnotify'
    'libstdc++'
    'libudev.so'
    'libusb'
    'libx11'
    'libxcb'
    'libxcomposite'
    'libxdamage'
    'libxext'
    'libxfixes'
    'libxkbcommon'
    'libxrandr'
    'mesa'              # Debian libgbm1
    'nspr'
    'nss'
    'pango'
    'vulkan-driver'     # Debian mesa-vulkan-drivers | vulkan-icd
    'vulkan-icd-loader'
    'xdg-utils'
    'xz'
)

optdepends=(
    'git: Codex Git/repository workflows'
)

_deb="chatgpt_${pkgver}_amd64.deb"
_upstream_base='https://persistent.oaistatic.com/codex-app-prod/linux/deb/pool/main/c/chatgpt'

source_x86_64=(
    "${_deb}::${_upstream_base}/${_deb}"
)

noextract=("${_deb}")

sha256sums_x86_64=(
    'da37b8e7bcefaaea019c478cacbe6c73ee1ddd15e0e1ebb3c7ef0a42dd818ac2'
)

# Preserve OpenAI's prebuilt binaries exactly.
options=('!strip' '!debug')

package() {
    local work="$srcdir/deb-unpack"
    local control="$work/control"
    local data="$work/data"
    local control_archive
    local data_archive
    local field

    rm -rf "$work"
    mkdir -p "$work"

    bsdtar -xf "$srcdir/$_deb" -C "$work"

    control_archive="$(
        find "$work" -maxdepth 1 -type f -name 'control.tar.*' -print -quit
    )"

    data_archive="$(
        find "$work" -maxdepth 1 -type f -name 'data.tar.*' -print -quit
    )"

    if [[ -z "$control_archive" ]]; then
        printf 'Unable to locate control.tar.* inside %s\n' "$_deb" >&2
        return 1
    fi

    if [[ -z "$data_archive" ]]; then
        printf 'Unable to locate data.tar.* inside %s\n' "$_deb" >&2
        return 1
    fi

    mkdir -p "$control"
    bsdtar -xf "$control_archive" -C "$control"

    [[ -f "$control/control" ]] || {
        printf 'Expected Debian control metadata is missing\n' >&2
        return 1
    }

    field="$(sed -n 's/^Package: //p' "$control/control")"
    [[ "$field" == 'chatgpt' ]] || {
        printf 'Unexpected Debian package name: %s\n' "$field" >&2
        return 1
    }

    field="$(sed -n 's/^Version: //p' "$control/control")"
    [[ "$field" == "$pkgver" ]] || {
        printf 'Debian version %s does not match pkgver %s\n' "$field" "$pkgver" >&2
        return 1
    }

    field="$(sed -n 's/^Architecture: //p' "$control/control")"
    [[ "$field" == 'amd64' ]] || {
        printf 'Unexpected Debian architecture: %s\n' "$field" >&2
        return 1
    }

    mkdir -p "$data"
    bsdtar -xf "$data_archive" -C "$data"

    [[ -x "$data/usr/lib/chatgpt/ChatGPT" ]] || {
        printf 'Expected ChatGPT executable is missing\n' >&2
        return 1
    }

    [[ -L "$data/usr/bin/chatgpt" ]] \
        && [[ "$(readlink "$data/usr/bin/chatgpt")" == '../lib/chatgpt/codex-launcher' ]] || {
        printf 'Expected /usr/bin/chatgpt launcher symlink is missing or changed\n' >&2
        return 1
    }

    [[ -x "$data/usr/lib/chatgpt/codex-launcher" ]] || {
        printf 'Expected codex-launcher is missing\n' >&2
        return 1
    }

    [[ -f "$data/usr/share/applications/chatgpt.desktop" ]] \
        && grep -qx 'Exec=chatgpt %U' "$data/usr/share/applications/chatgpt.desktop" \
        && grep -qx 'Icon=chatgpt' "$data/usr/share/applications/chatgpt.desktop" || {
        printf 'Expected ChatGPT desktop entry is missing or changed\n' >&2
        return 1
    }

    [[ -f "$data/usr/share/pixmaps/chatgpt.png" ]] || {
        printf 'Expected ChatGPT icon is missing\n' >&2
        return 1
    }

    if find "$data/usr/lib/chatgpt" \
        \( -type f -o -type d \) \
        \( -perm /6000 -o -perm /0002 \) -print -quit | grep -q .; then
        printf 'Refusing payload containing set-id or world-writable paths\n' >&2
        return 1
    fi

    install -d \
        "$pkgdir/usr/bin" \
        "$pkgdir/usr/lib" \
        "$pkgdir/usr/share/applications" \
        "$pkgdir/usr/share/pixmaps"

    # Copy only the upstream application payload required on Arch/Artix.
    # Debian APT integration, maintainer state, and AppArmor files are
    # intentionally not copied into the package.
    cp -a --no-preserve=ownership \
        "$data/usr/lib/chatgpt" \
        "$pkgdir/usr/lib/"

    cp -a --no-preserve=ownership \
        "$data/usr/bin/chatgpt" \
        "$pkgdir/usr/bin/"

    install -Dm644 \
        "$data/usr/share/applications/chatgpt.desktop" \
        "$pkgdir/usr/share/applications/chatgpt.desktop"

    install -Dm644 \
        "$data/usr/share/pixmaps/chatgpt.png" \
        "$pkgdir/usr/share/pixmaps/chatgpt.png"

    # Preserve upstream's third-party copyright notice without treating it as
    # the license for the proprietary ChatGPT application.
    install -Dm644 \
        "$data/usr/share/doc/chatgpt/copyright" \
        "$pkgdir/usr/share/doc/$pkgname/third-party-notices"
}
