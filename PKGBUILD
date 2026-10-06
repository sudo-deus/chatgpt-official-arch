# SPDX-License-Identifier: 0BSD
# Maintainer: sudo-deus

pkgname=chatgpt-official-bin
pkgver=26.930.61225
pkgrel=2
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
    'openssl'           # Debian libssl3
    'nss'
    'pango'
    'tpm2-tss'          # Debian libtss2-*
    'vulkan-driver'     # Debian mesa-vulkan-drivers | vulkan-icd
    'vulkan-icd-loader'
    'xdg-utils'
    'xz'
)

makedepends=('python' 'curl')

optdepends=(
    'git: Codex Git/repository workflows'
    'python: bundled optional helper scripts'
)

_deb="chatgpt_${pkgver}_amd64.deb"
_upstream_base='https://persistent.oaistatic.com/codex-app-prod/linux/deb/pool/main/c/chatgpt'

source_x86_64=(
    "${_deb}::${_upstream_base}/${_deb}"
)

source=(
    'upstream.py'
    'upstream-depends.txt'
    'upstream-layout.json'
)
sha256sums=(
    '94b77e970c265538520cd45da34da768bb350336abd88684b82f467a918a5655'
    '56b635089fe2c09131910030f7a1f7bb6caf77d5672f0ff0fadddd7edfb62e1b'
    '956e33c31ead6961bf564ea9043acc79c4502d21046a626a8ea62f58d91fda1e'
)
noextract=("${_deb}")

sha256sums_x86_64=(
    'b90a80f9353bc12a5a5b8469502a8e5794a3c54a371c8880e094d500de695bb8'
)

# Preserve OpenAI's prebuilt binaries exactly.
options=('!strip' '!debug')

package() {
    local work="$srcdir/deb-unpack"
    rm -rf "$work"
    python3 "$srcdir/upstream.py" deb "$srcdir/$_deb" "$pkgver" \
        "$srcdir/upstream-depends.txt" "$srcdir/upstream-layout.json" "$work/data" || return 1
    local data="$work/data"

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
