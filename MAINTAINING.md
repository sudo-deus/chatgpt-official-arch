# Maintainer guide

The updater detects releases; it never edits the recipe or publishes packages.

## Update checklist

1. Run `scripts/check-upstream.sh`. Read `Version`, `Filename`, and `SHA256`
   from OpenAI's uncompressed `Packages` index. Do not package the mutable
   `latest/` URL.
2. Confirm that the versioned pool URL exists, then update `pkgver`, reset
   `pkgrel` to `1`, and replace `sha256sums_x86_64`.
3. Regenerate metadata with `makepkg --printsrcinfo > .SRCINFO` and run
   `tests/test-check-upstream.sh` after updating its current fixture.
4. Run `makepkg --verifysource`, then build in a clean Arch environment. For
   official Arch tooling, use `extra-x86_64-build`; otherwise use a disposable
   clean chroot or container with an unprivileged build user.
5. Run `namcap PKGBUILD` and `namcap chatgpt-official-bin-*.pkg.tar.zst`.
   Review every warning instead of suppressing it mechanically.
6. Inspect `pacman -Qip`, `pacman -Qlp`, and `bsdtar -tvf` output. The package
   may contain only `/usr/lib/chatgpt`, `/usr/bin/chatgpt`, the desktop entry,
   icon, and third-party notices. Verify root ownership, normal modes, no
   set-id/world-writable paths, and no APT, RPM, maintainer, or AppArmor state.
   Run `tests/test-package.sh chatgpt-official-bin-*.pkg.tar.zst` for the
   automated baseline, then review the listings manually.
7. Install only after fully quitting ChatGPT. Smoke-test sign-in, local Codex
   commands, a Git repository workflow, URL handling, notifications, and
   XWayland. Test native Wayland separately with
   `chatgpt --ozone-platform=wayland`.

## Safe upgrade and rollback

Keep the previous pacman package. Before testing an update on the maintainer
machine, back up `~/.codex` and the app's `Codex` directory under the active
`$XDG_CONFIG_HOME`. Fully quit ChatGPT/Codex before running `pacman -U`;
replacing files underneath a running app can mix old processes with newly
spawned helper binaries.

If smoke tests fail, fully quit the app and reinstall the retained package.
Restore the state backup only if an application data migration prevents the
older version from starting or reading its state.

Do not commit downloaded `.deb` files, generated pacman packages, credentials,
or state backups.
