# ChatGPT Official Linux Binary for Arch/Artix

Pacman packaging for OpenAI's official ChatGPT Linux desktop application.

This project downloads OpenAI's official, versioned Debian package and
repackages only its application payload for installation on Arch Linux and
Artix Linux. It is not a web wrapper, does not modify the application binaries,
and does not redistribute the upstream `.deb` or generated pacman packages.

This packaging is unofficial, unsupported by OpenAI, and not affiliated with
OpenAI. OpenAI's Linux app is currently a preview with formal support for
selected Ubuntu, Debian, and Fedora releases; other distributions may work but
are not formally supported. See the
[official Linux documentation](https://learn.chatgpt.com/docs/linux/linux-app).

## Why this exists

Installing the Debian package directly on an Arch-based system would also
introduce Debian-specific repository configuration and maintainer integration.
This PKGBUILD copies the application, launcher, desktop entry, icon, and
third-party notices while intentionally omitting APT, RPM, maintainer, and
AppArmor state.

The source is an immutable OpenAI pool URL, not the mutable `latest/` download.
`makepkg` verifies the pinned SHA-256 before unpacking it. The package step also
checks the Debian package name, version, architecture, launcher layout, desktop
entry, icon, and unsafe file modes so upstream layout changes fail closed.

## Supported target

- Arch Linux or Artix Linux
- x86-64
- a graphical desktop environment
- a working Vulkan driver

OpenAI also publishes ARM64 packages, but this recipe remains x86-64-only until
ARM64 has been tested on an Arch-derived system.

## Build and install

Verify and build as an unprivileged user:

```sh
makepkg --verifysource
makepkg
```

Inspect the result before installation:

```sh
pacman -Qip ./chatgpt-official-bin-*.pkg.tar.zst
pacman -Qlp ./chatgpt-official-bin-*.pkg.tar.zst
namcap PKGBUILD
namcap ./chatgpt-official-bin-*.pkg.tar.zst
```

Do not replace the package underneath a running ChatGPT/Codex process. Fully
quit the app, retain the previous package for rollback, and then install:

```sh
sudo pacman -U ./chatgpt-official-bin-*.pkg.tar.zst
```

Remove it normally with `sudo pacman -R chatgpt-official-bin`.

## Updates

Run `scripts/check-upstream.sh` to compare the PKGBUILD with OpenAI's
uncompressed Debian `Packages` index. Exit status `0` means current, `10` means
an update is available, and any other nonzero status means validation failed.

The scheduled GitHub workflow opens or updates a tracking issue when upstream
changes. It never modifies the recipe, commits a bump, builds a release, or
publishes artifacts. Releases remain human-reviewed; see
[MAINTAINING.md](MAINTAINING.md).

## Wayland

The app uses XWayland by default when it is available in a Wayland session.
Native Wayland remains experimental upstream and can be tested after fully
quitting the app:

```sh
chatgpt --ozone-platform=wayland
```

Floating windows, positioning, focus, and shortcuts may behave differently in
native Wayland mode.

## Licensing

The packaging source in this repository is licensed under
`0BSD`; see
[LICENSE](LICENSE). That license does not apply to ChatGPT or its bundled
components. OpenAI's Debian package does not currently ship a license for the
proprietary ChatGPT application, so the PKGBUILD reports its license as
`unknown` and installs the bundled Electron notice only as a third-party notice.

## Current release

- Upstream version: `26.908.40834`
- Upstream SHA-256:
  `da37b8e7bcefaaea019c478cacbe6c73ee1ddd15e0e1ebb3c7ef0a42dd818ac2`
- Approximate installed size: 1.35 GiB

Downloaded packages, build trees, package archives, logs, and state backups are
excluded from Git.
