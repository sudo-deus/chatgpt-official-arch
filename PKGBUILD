pkgname=chatgpt-official-bin
pkgver=26.901.51231
pkgrel=1
pkgdesc="Official ChatGPT desktop app for Linux, repackaged for Arch/Artix"
arch=('x86_64')
url='https://developers.openai.com/codex/app'
license=('custom')

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
    'libglvnd'
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
    'mesa'
    'nspr'
    'nss'
    'pango'
    'vulkan-driver'
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
    '62580188d87c3d3a9369dab7c73b42a8a32518d4df8a2d5bae6466ddeac5c05e'
)

# Preserve OpenAI's prebuilt binaries exactly.
options=('!strip' '!debug')

package() {
    local work="$srcdir/deb-unpack"
    local data="$work/data"
    local data_archive

    rm -rf "$work"
    mkdir -p "$work"

    bsdtar -xf "$srcdir/$_deb" -C "$work"

    data_archive="$(
        find "$work" -maxdepth 1 -type f -name 'data.tar.*' -print -quit
    )"

    if [[ -z "$data_archive" ]]; then
        printf 'Unable to locate data.tar.* inside %s\n' "$_deb" >&2
        return 1
    fi

    mkdir -p "$data"
    bsdtar -xf "$data_archive" -C "$data"

    [[ -x "$data/usr/lib/chatgpt/ChatGPT" ]] || {
        printf 'Expected ChatGPT executable is missing\n' >&2
        return 1
    }

    [[ -L "$data/usr/bin/chatgpt" ]] || {
        printf 'Expected /usr/bin/chatgpt symlink is missing\n' >&2
        return 1
    }

    install -d \
        "$pkgdir/usr/bin" \
        "$pkgdir/usr/lib" \
        "$pkgdir/usr/share/applications" \
        "$pkgdir/usr/share/pixmaps"

    # Copy only the upstream application payload required on Arch/Artix.
    # Debian APT integration, maintainer state, and AppArmor files are
    # intentionally not copied into the package.
    cp -a \
        "$data/usr/lib/chatgpt" \
        "$pkgdir/usr/lib/"

    cp -a \
        "$data/usr/bin/chatgpt" \
        "$pkgdir/usr/bin/"

    install -Dm644 \
        "$data/usr/share/applications/chatgpt.desktop" \
        "$pkgdir/usr/share/applications/chatgpt.desktop"

    install -Dm644 \
        "$data/usr/share/pixmaps/chatgpt.png" \
        "$pkgdir/usr/share/pixmaps/chatgpt.png"

    # Preserve the copyright notice shipped by OpenAI's Debian package.
    # This is primarily Electron's MIT notice and is not treated here as
    # evidence that the ChatGPT application itself is MIT-licensed.
    install -Dm644 \
        "$data/usr/share/doc/chatgpt/copyright" \
        "$pkgdir/usr/share/doc/$pkgname/copyright"
}
