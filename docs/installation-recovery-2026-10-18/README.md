# Installation recovery reports — 2026-10-18

The installation evidence was reviewed and relevant findings were sent to the CachyOS **New-Cli-Installer** project with the system owner's authorization. GitHub accepted the submissions; no maintainer acknowledgement or acceptance of a fix is claimed.

## Submitted findings

| Finding | Action | Upstream link |
|---|---|---|
| Optimized repository configuration used for base installation was missing from the target; GNOME transaction then hit a libnma version conflict | Added corroborating znver4 evidence and the successful operational recovery to existing issue #50, avoiding a duplicate | https://github.com/CachyOS/New-Cli-Installer/issues/50#issuecomment-6255284025 |
| Selected desktop installation failure was downgraded to a warning and installation reported completion/success | Opened issue #51 describing the error contract, source inspection, recovery and proposed regression test | https://github.com/CachyOS/New-Cli-Installer/issues/51 |

The submitted texts are preserved in [repositorios-comment.md](repositorios-comment.md) and [desktop-issue.md](desktop-issue.md).

## Evidence and limits

Native installer version recorded during installation: `0.12.4-bb3eccb-20260804`; package `cachyos-cli-installer-new 0.12.4-1`. Configuration: headless GNOME / UEFI / btrfs on a znver4-capable CPU, using a personal CachyOS remaster with a Codex wrapper. The retained log contains a GNOME pacstrap dependency conflict between `libnma-common 1.10.6-3` and installed `libnma-gtk4` requiring `libnma-common=1.10.6-3.1`, followed by completion messages and a desktop warning. The installation audit records native exit status 0.

Recovery: preserve target configuration and a pre-repair btrfs snapshot; restore matching optimized repository configuration; perform a full system upgrade while installing missing desktop packages; validate the installed packages/files, dependency database and enabled display manager. The repair log records GNOME Shell and libnma installed; post-repair checks report no dependency database errors or missing GNOME/GDM package files and GDM enabled. This is a tested operational recovery, not a compiled/tested upstream source patch.

Source review used upstream commit `8530fd133a7177d1cf0767659eb1355ffcd53a58`:

- [Configuration generation and host-file copying](https://github.com/CachyOS/New-Cli-Installer/blob/8530fd133a7177d1cf0767659eb1355ffcd53a58/gucc/src/install.cpp)
- [Base install copy source](https://github.com/CachyOS/New-Cli-Installer/blob/8530fd133a7177d1cf0767659eb1355ffcd53a58/installer-lib/src/packages.cpp)
- [Desktop errors recorded as warnings](https://github.com/CachyOS/New-Cli-Installer/blob/8530fd133a7177d1cf0767659eb1355ffcd53a58/installer-lib/src/orchestrator.cpp)
- [Headless exit status derived from success](https://github.com/CachyOS/New-Cli-Installer/blob/8530fd133a7177d1cf0767659eb1355ffcd53a58/src/main.cpp)

No destructive reinstall was performed to reproduce these findings on current master. Historical source/log evidence and suggested future tests are identified as such.

## Other reviewed corrections

- Missing Konsole in the custom administrator launcher: a local integration defect; switched to the installed GNOME terminal. Not submitted as an upstream CachyOS defect.
- Credential-console retries and maintenance/publication wiring: integration-specific behavior, not evidence of a native CachyOS defect.
- Keyboard/account preferences, gaming packages and OpenAI desktop installation: configuration/provisioning work, not upstream bug reports.
- Package signature policy and private directory permissions: local hardening; no evidence establishing an upstream vulnerability was submitted.
- Mirror HTTP 404/connectivity failures: transient events; final transactions completed. Insufficient evidence for an independent reproducible defect.
- Headless Vulkan display warnings: hardware enumeration succeeded, and a graphical display was absent in that test; no claim of a graphics driver defect or performance improvement.

Only selected technical excerpts are public. Private raw logs, credentials, personal account details and disk serials were not uploaded. Prepared with substantial Codex assistance.
