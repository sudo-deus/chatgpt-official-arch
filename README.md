# ChatGPT for Arch/Artix

Unofficial x86-64 packaging of OpenAI's prebuilt ChatGPT Linux desktop app for
Arch Linux and Artix Linux. Requires a graphical desktop and a working Vulkan
driver. The recipe downloads a versioned Debian package and verifies its SHA-256.

## Install

Install `base-devel`, `git`, `python`, and `curl`, then build as a regular user:

```sh
git clone https://github.com/sudo-deus/chatgpt-official-arch.git
cd chatgpt-official-arch
makepkg -s
```

Quit ChatGPT before installing:

```sh
sudo pacman -U "$(makepkg --packagelist)"
```

## Updates

A daily GitHub workflow validates changed upstream releases and creates or
refreshes one update PR. A maintainer reviews and merges it. Dependency or
integration changes stop automation for manual review.

Check upstream locally:

```sh
scripts/check-upstream.sh
```

Exit codes: `0` current, `10` update available, `1` invalid metadata or another
failure. After an update PR is merged:

```sh
git pull --ff-only
makepkg -sf
# Quit ChatGPT, then:
sudo pacman -U "$(makepkg --packagelist)"
```

The app downloads its Codex primary runtime separately on startup. Runtime
versions and downloads are application-managed and independent of this package.

## Remove

```sh
sudo pacman -R chatgpt-official-bin
```

## Wayland

Native Wayland can be tested after quitting the app:

```sh
chatgpt --ozone-platform=wayland
```

Window positioning, focus, and shortcuts may differ from XWayland.

## Maintenance

See [MAINTAINING.md](MAINTAINING.md) for validation, automation setup, dependency
review, and rollback.

## License

Repository-owned packaging code is [0BSD](LICENSE). This does not license
OpenAI's proprietary application or its bundled components. The package retains
upstream third-party notices and uses `license=('unknown')` for the application.
