## Observed behavior

During a headless GNOME installation, the desktop package transaction failed, but the installer later printed `Installation complete!` and the wrapper recorded native exit status 0. An automation that trusts the exit status can therefore accept an installation whose requested desktop was not installed.

Version: `cachyos-installer 0.12.4-bb3eccb-20260804`, package `cachyos-cli-installer-new 0.12.4-1`. Environment: personal August 2026 CachyOS remaster with a Codex wrapper invoking the native headless installer; UEFI, btrfs, GNOME, znver4-capable CPU. This was **not** an unmodified ISO. This report is based on the retained installation evidence, not a fresh installation on current master.

## Evidence

Selected native installer log lines, with personal information omitted:

```text
error: failed to prepare transaction (could not satisfy dependencies)
:: installing libnma-common (1.10.6-3) breaks dependency 'libnma-common=1.10.6-3.1' required by libnma-gtk4
==> ERROR: Failed to install packages to new root
install_desktop_packages: failed to install packages: ...
Installation finished. No error reported.
[100.0%] Installation complete!
Install orchestrator finished.
install warning: install_desktop_packages: failed to install packages: ...
```

The installation audit separately records native exit status 0. The repository-configuration trigger is already reported in #50; this issue concerns the success/error contract after a selected desktop fails, independently of that particular dependency problem.

## Expected behavior and proposed fix

For a desktop explicitly selected by the user, propagate a failed desktop transaction as an unsuccessful installation/nonzero headless exit status, or provide an explicit machine-readable incomplete result that cannot be confused with full success. Preserve cleanup and diagnostic logs. Missing selected desktop/display-manager packages should be checked before reporting completion.

At reviewed master `8530fd133a7177d1cf0767659eb1355ffcd53a58`, `installer-lib/src/orchestrator.cpp` records desktop-step errors as warnings and ultimately returns `success = true`; `src/main.cpp` returns 0 when `result.success` is true. This supports the observed behavior by source inspection. I have not built a source fix or run a failure-injection test.

Suggested regression test: inject a failed desktop package transaction through the test runner, then assert unsuccessful headless status, no unconditional completion claim, and cleanup/log preservation. Keep intentional server/no-desktop installations valid.

## Recovery applied and validation

The operational recovery was to back up the target, restore consistent optimized repository configuration, then perform a full `pacman -Syu --needed` transaction installing the missing GNOME/GDM packages. Post-repair checks found the requested packages present, GNOME/GDM files present, no dependency database errors, and GDM enabled. No dependencies were ignored or forced. This recovered the installed system; it does not fix the installer's error-propagation behavior.

No new disk installation was performed for this report. To reproduce safely, use a disposable VM/test target with GNOME selected and an injected desktop package failure, rather than rerunning an installation on an existing personal system.

Prepared with substantial Codex assistance and submitted with the system owner's authorization. No raw private logs or credentials are attached.

<!-- cachyos-codex-lab-install-20261018-desktop-status -->
