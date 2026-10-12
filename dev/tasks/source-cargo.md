# Source: Cargo (`~/.cargo/bin`)

- **Task ID:** `source-cargo`
- **Status:** done
- **Related:** `bins` already lists `~/go/bin` and `~/.local/bin`; Cargo is the Rust equivalent

## Problem

Many CLI tools on a Mac (ripgrep, fd, bat, …) are installed with `cargo install` and never
touch Homebrew. They live under `~/.cargo/bin` and are invisible to vole today unless the
user also copied a symlink elsewhere.

## Goal

`vole scan` lists Cargo user installs, with a best-effort version, under source id `cargo`.
One inventory entry per **package** (multi-bin crates are a single row).

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Enumerate via `cargo install --list` or by reading `~/.cargo/bin`? | locked | **`cargo install --list`** when `cargo` is on PATH (package + version); fall back to listing `~/.cargo/bin` (binary names, no version) if cargo is missing but the bin dir exists |
| 2 | Entry name = Cargo package or binary name? | locked | **Package name** from `--list` (one entry per package, even if it installs several bins). Directory fallback has only binary names — use those |
| 3 | Skip crates that are also brew formulae when the name collides? | locked | **No** — first source wins (brew is registered first); Cargo only appears if brew did not claim the name |

## Non-goals

- Not tracking project-local `target/` builds.
- Not `rustup` toolchains as separate inventory (optional follow-up).

## Implementation

- New `vole/sources/cargo.py` → `Installed('cargo', name, versions)`.
- Register in `vole/sources/__init__.py` after brew/apps (order preserved for first-wins).
- Fixture or mocked `cargo install --list` output in tests.
- README Sources bullet.

## Done when

- [x] Scan discovers Cargo installs when present; no-op when neither `cargo` nor `~/.cargo/bin` exists.
- [x] Tests cover parse of `--list` (and empty / missing cargo).
- [x] README Sources updated.

## Notes

```
$ cargo install --list
ripgrep v14.1.0:
    rg
fd-find v10.1.0:
    fd
```
