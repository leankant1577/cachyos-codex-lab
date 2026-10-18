Additional evidence for #50: the same configuration mismatch affected a GNOME installation on a znver4-capable machine, with a concrete dependency failure during desktop installation.

Environment: `cachyos-installer 0.12.4-bb3eccb-20260804`, package `cachyos-cli-installer-new 0.12.4-1`, headless GNOME / UEFI / btrfs. This was a personal remaster of the August 2026 ISO with a Codex wrapper calling the native installer, rather than an unmodified ISO. The observation is from the recorded installation; I have not repeated a destructive installation against current master.

Selected installation-log evidence, with personal data omitted:

```text
CachyOS cachyos-znver4 Repo added to /tmp/cachyos-installer-pacman.conf
[base package selection]
cachyos-extra-znver4/libnma-common 1.10.6-3.1
cachyos-extra-znver4/libnma-gtk4   1.10.6-3.1
[desktop transaction]
pacstrap -c -C /mnt/etc/pacman.conf /mnt ... libnma ...
error: failed to prepare transaction (could not satisfy dependencies)
:: installing libnma-common (1.10.6-3) breaks dependency 'libnma-common=1.10.6-3.1' required by libnma-gtk4
==> ERROR: Failed to install packages to new root
```

Recovery that worked on this installation:

1. Preserve the target configuration and a pre-repair btrfs snapshot.
2. Restore the matching optimized repository configuration in the target's `pacman.conf`, with the correct repository priority and corresponding mirrorlists.
3. Run a **full system upgrade together with the missing desktop installation** in the target. The recorded transaction used `pacman -Syu --needed` with GNOME/GDM and the related packages. No ignored dependencies, forced package replacement, or standalone partial upgrade was used.
4. Verify package presence/files and dependency consistency, and enable GDM. The repair log records `gnome-shell 1:51.1-1.1` and `libnma 1.10.6-3.1`; the post-repair checks report no dependency database errors, no missing GNOME/GDM package files, and GDM enabled.

The proposed upstream direction in this issue—persist the generated configuration used by the base transaction before later desktop/package transactions—matches this failure. It should have a regression test for consistent repository configuration across base installation, desktop installation and the installed target. This report supplies a tested operational recovery, **not a built/tested upstream source patch**.

Reviewed source: `8530fd133a7177d1cf0767659eb1355ffcd53a58`; `gucc/src/install.cpp` generates the temporary config and then copies `host_files_to_copy`, while `installer-lib/src/packages.cpp` supplies the live `/etc/pacman.conf` as that copy source.

Prepared with substantial Codex assistance and submitted with the system owner's authorization. No raw private logs or credentials are attached.

<!-- cachyos-codex-lab-install-20261018-repository-evidence -->
