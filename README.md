# ChatGPT Official Linux Binary for Arch/Artix

Pacman packaging for OpenAI's official ChatGPT Linux desktop application.

This project downloads OpenAI's official Debian package and repackages its application payload for installation on Arch Linux and Artix Linux.

It is **not** a web wrapper, does not modify the ChatGPT application binaries, and does not redistribute the upstream `.deb`.

This project is unofficial, unsupported by OpenAI, and is not affiliated with OpenAI.

## Why this exists

OpenAI publishes an official Linux desktop application as a Debian package, but does not currently provide an Arch/Artix package.

Installing the Debian package directly is undesirable on Arch-based systems because it also contains Debian-specific package-management integration, including APT repository configuration and maintainer scripts.

This PKGBUILD extracts only the application payload needed to run ChatGPT under pacman.

The Debian-specific APT integration and AppArmor configuration are intentionally omitted.

## Requirements

- Arch Linux or Artix Linux
- x86-64
- `makepkg`
- pacman
- a working graphical desktop environment
- a working Vulkan driver for the GPU

## Building

Verify the pinned upstream source:

    makepkg --verifysource

Build the package:

    makepkg

The PKGBUILD downloads the exact versioned OpenAI `.deb` directly from OpenAI and verifies it against a pinned SHA-256 checksum.

Install the resulting package:

    sudo pacman -U ./chatgpt-official-bin-*.pkg.tar.zst

Remove it normally:

    sudo pacman -R chatgpt-official-bin

## Current version

Upstream ChatGPT version:

    26.901.51231

Upstream SHA-256:

    62580188d87c3d3a9369dab7c73b42a8a32518d4df8a2d5bae6466ddeac5c05e

The package is fetched from OpenAI's versioned Debian package repository rather than a mutable `latest` URL.

## Tested

The package has been built successfully on:

- Artix Linux
- dinit
- Hyprland 0.56.2
- AMD Ryzen 5 PRO 6650U
- AMD Radeon 660M graphics

Verified so far:

- upstream `.deb` SHA-256 validation
- clean build directly from OpenAI's remote source
- pacman package generation
- expected `/usr/bin/chatgpt` launcher
- expected application payload
- desktop entry and icon
- required dependencies resolve on the test system
- no Debian APT integration is packaged
- no Debian AppArmor profile is packaged

Runtime verified on the test system:

- application starts and renders normally
- OpenAI account login succeeds
- authenticated sessions work normally
- networking works
- Chromium/Electron GPU process starts successfully
- ChatGPT runs through XWayland under a Wayland Hyprland session
- existing Firefox HTTP/HTTPS/HTML defaults remain unchanged
- application configuration is isolated under the Hyprland XDG environment
- normal application interaction and filesystem use work

## Notes

The official desktop application is large. The current package is approximately 507 MiB compressed and 1.35 GiB installed.

OpenAI's application binaries are preserved without stripping or modification.

Downloaded `.deb` files, built pacman packages, `src/`, and `pkg/` are intentionally excluded from Git.

## Support

Arch Linux and Artix Linux are not officially supported targets for OpenAI's Linux desktop package.

This packaging project is unofficial and is not affiliated with OpenAI.
