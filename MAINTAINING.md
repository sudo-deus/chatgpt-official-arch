# Maintainer guide

## Validation

Build as an unprivileged user. Fast checks need `makepkg`, Python, and Bash:

```sh
scripts/validate.sh
```

Full validation additionally needs `namcap`, `zstd`, and network access:

```sh
scripts/validate.sh --full
```

The full path verifies checksums, rebuilds the package, checks archive contents,
and reports namcap diagnostics. CI installs recipe dependencies before building.
This is not a runtime smoke test. On a desktop, use `makepkg -s` to install build/runtime dependencies.
No workflow retains or publishes application binaries.

## Automated updates

The daily and manually dispatched upstream workflow starts from the default
branch and queries OpenAI's Debian index. It changes only `pkgver`, `pkgrel`, the
amd64 checksum, and generated `.SRCINFO`. The fixed branch
`automation/chatgpt-upstream` and its open PR are refreshed only after full
validation. Concurrent runs are serialized. A changed default-branch revision
aborts publication; rerun the workflow.

A new version resets `pkgrel` to `1`. A changed checksum at the same version
increments `pkgrel` once and is prominently disclosed in the PR. Review such
replacements carefully. Older upstream releases and ambiguous metadata fail.

Validation uses a read-only token. Publication has only `contents: write` and
`pull-requests: write`; its metadata patch is independently reproduced before
publication. The short-lived Actions handoff contains only recipe metadata and
validation reporting. No PAT is required.

Under **Settings → Actions → General → Workflow permissions**, enable
**Allow GitHub Actions to create and approve pull requests**. The workflows do
not approve or merge PRs. Organization policy may prevent this setting. Leave
the default token permission read-only; the publication job requests its own
specific write permissions.

PRs and commits created with `GITHUB_TOKEN` do not reliably trigger ordinary
push/PR workflows. Required checks therefore run inside the updater before the
PR is created. Independent push/PR checks remain enabled; manually dispatch full
validation if required by branch protection or after human edits.

Dependency, layout, or validation failures appear in the failed workflow step
and summary. The prior automation branch remains intact when validation fails.
Resolve the underlying change in a reviewed maintainer change; do not relax an
assertion just to make the update pass. If publishing a validated branch succeeds
but GitHub rejects PR creation, enable the setting above and rerun.

## Troubleshooting update failures

Install Git in the Arch container **before** `actions/checkout` in every job.
Without Git, checkout falls back to a REST source archive without `.git`.
Installing Git afterwards does not recreate the repository or history: PR scope
checks, the updater's base revision check, and publication then fail. Keep the
post-checkout repository check and assign ownership to the unprivileged builder
after checkout.

Scope detection runs full package validation when the event's comparison commit
is unavailable. A force-push can remove the previous tip from all fetched refs,
so even a full-history checkout cannot guarantee that `github.event.before`
exists. New branches, missing history, and manual dispatches therefore take the
full path; ordinary documentation-only diffs can still use fast checks. Other
Git failures remain errors rather than silently skipping validation.

A dependency-drift error is a request to review the upstream change. For example,
release `26.1013.40934` raised Debian's GLib minimum from `2.39.4` to `2.49.3`.
The reviewed Arch mapping is `glib2>=2.49.3`; the Debian baseline and its local
source checksum were updated together. The new release also updated bundled
Sharp/libvips and optional Python helpers. Their precise namcap findings were
reviewed against ELF dependencies and source imports before updating the policy.
Keep these checks strict for future releases.

Release `26.1027.51404` made Debian's `libglib2.0-bin` mandatory and reordered
and deduplicated its dependency list. The existing Arch/Artix `glib2` dependency
already supplies `gio`, `gsettings`, `gdbus`, and `glib-compile-schemas`; the
reviewed baseline and its source checksum were updated with the release.
New LaTeX preview and optional dictation helpers were reviewed before adding
their exact Python findings to the namcap policy. Future drift still fails.

After a GitHub username change, update the local `origin` URL and repository
links. Workflows use `github.repository`/the event repository, so their owner is
resolved automatically. SSH still needs an available, unlocked existing key;
a missing agent or passphrase prompt is separate from an incorrect remote URL.

## Local updates and reviewed baselines

```sh
scripts/check-upstream.sh --json
scripts/update-upstream.sh --json
scripts/validate.sh --full
```

The updater is idempotent and regenerates `.SRCINFO` through
`makepkg --printsrcinfo`. Tests use isolated fixtures rather than the live recipe
version. Never hand-edit `.SRCINFO`.

`upstream-depends.txt` records reviewed Debian `Depends`. Whitespace
and continuation lines are normalized, preserving alternatives and version
constraints. The index and downloaded control metadata must both match. The
updater cannot modify this baseline or the Arch dependency array.

The Arch mapping uses `glibc` for libc6; `gtk3`, `glib2`, `at-spi2-core`, and
`gdk-pixbuf2` for GTK/GLib/accessibility requirements; `libxcb` for libxcb1 and
libxcb-dri3-0; and `libx11` for libx11-6 and libx11-xcb1. `mesa` supplies GBM,
`libglvnd` supplies libGL, and `vulkan-driver` plus `vulkan-icd-loader` covers
Vulkan. `openssl` covers libssl3 and `tpm2-tss` covers libtss2-*.
The launcher may load libraries dynamically, so namcap alone cannot establish
that a declared dependency is unused. Optional Qt shim warnings and proprietary
runtime components must be reviewed against the actual packaged ELF files.
`tests/fixtures/namcap-reviewed.json` records specific reviewed findings and
reasons. New findings fail, even when namcap exits successfully; never refresh
this policy mechanically from an unreviewed log.

For dependency drift, inspect both metadata and ELF requirements (`readelf -d`),
review Arch package ownership/version constraints, then deliberately update the
mapping and baseline. Do not map Debian names automatically. Recompute local
source checksums after helper or baseline edits, then regenerate `.SRCINFO`.

`upstream-layout.json` records desktop fields, required application
files, and the complete external-file inventory. Metainfo, swcatalog, lintian,
and AppArmor files are reviewed exclusions. New external integration files or
changed desktop/protocol declarations fail rather than being silently copied.
Only the application tree, launcher, desktop entry, icon, and third-party notice
are packaged. APT/RPM configuration and maintainer scripts remain excluded.

Archive validation rejects traversal, duplicate destinations, extraction through
symlinks, unsupported file types, non-root ownership, and unsafe modes. Required
application files and integration fields are checked before extraction. Inspect
new integration explicitly before changing an expectation.

## Desktop testing and rollback

After reviewing package contents and diagnostics, quit ChatGPT and retain the
previous pacman package before installing. Smoke-test authentication, local
Codex commands, Git workflows, URL handling, notifications, and XWayland. Test
native Wayland separately. CI does not authenticate or launch the desktop.

Back up `~/.codex` and the app's `Codex` directory under `$XDG_CONFIG_HOME`
(default `~/.config`) before a potentially incompatible upgrade. For rollback,
quit the app and reinstall the retained package. Restore state only if a data
migration prevents the older version from working.

The separately downloaded Codex primary runtime is application-managed state.
Do not add its version, download, or checksum to PKGBUILD automation.

## Source licensing and repository hygiene

REUSE metadata covers repository-owned files only. `LICENSE`/`LICENSES/0BSD.txt`
do not license the proprietary desktop app, runtime, or third-party bundles.
Do not invent an application license identifier.

Before submitting changes, run `git diff --check`, inspect the complete diff,
and check `git status --short`. Downloaded Debian archives, build trees, pacman
packages, logs, caches, and state backups must stay untracked.
