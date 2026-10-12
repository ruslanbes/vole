# Pre-release code review (before v0.1.0)

- **Task ID:** `pre-release-review`
- **Status:** done (for `v0.1.0`; task doc kept)
- **Parent / blocked by:** unblocked `homebrew-formula` once `v0.1.0` is tagged

## Problem

The codebase grew fast over a few days (12 sources, 4 signals, 7 CLI verbs). Before the first
public tag it is worth one pass for dead code, things that will not scale, anything that touches
user data unsafely, and decisions that will be painful to change after people have inventories.

Review covered: `vole/` (all modules), `install.sh`, `bin/vole`, `tests/`, git metadata, docs
links. Tests pass on 3.9 (`/usr/bin/python3`) and 3.13. No findings are release-stopping bugs
in the happy path; several are release-stopping for credibility (broken doc links, exec bits) or
correctness on Intel Macs.

## Goal

Every item below is either fixed, consciously deferred (noted here), or turned into its own task.
Then cut `v0.1.0`.

## Findings

Severity: **B** = fix before tag, **S** = should fix soon, **N** = nice to have / watch.

Finding status: `open` | `deferred` | `done` | `won't fix`.

### 1. Correctness / future problems

| # | Sev | Where | Finding | Suggested fix | Status |
|---|-----|-------|---------|---------------|--------|
| 1.1 | **B** | `sources/brew.py:27`, `signals/spotlight.py:10` | Caskroom hardcoded to `/opt/homebrew/Caskroom`. Intel Macs use `/usr/local/Caskroom`; custom prefixes exist. Cask↔app dedup and cask usage signals silently break there | Resolve once via `$HOMEBREW_PREFIX` → `brew --prefix` → try both known paths; cache in one helper (`vole/brew_env.py` or inside `sources/brew.py`) and reuse in spotlight | done |
| 1.2 | **B** | `docs/adr/README.md` | Index links to `adr-001…007` files that **do not exist**. `dev/README.md` and several task docs also link them. Broken links on GitHub from day one | Either write the seven ADRs from the locked decisions in task docs (they are all already decided) or trim the index to what exists. Writing them is the honest fix; the content is in `architecture-review.md`, `storage-format.md`, `switch-to-json.md`, `python-only-restructure.md` | done — links removed, index emptied |
| 1.3 | **B** | `vole/__init__.py`, `cli.py` | `__version__ = '0.0.0'` and no `vole --version`. Homebrew `test do` and users need it; release runbook bumps a version that nothing reads | Set `__version__` from the release; add `--version` to the parser; make `dev/RELEASE.md` mention the bump | done — bump to `0.1.0` happens at release |
| 1.4 | **S** | `cli.py cmd_list` | `list` iterates **`versions.json`** as the installed set. Anything with no detectable version (plain `~/.local/bin` scripts, apps without `CFBundleShortVersionString`, cargo bin-dir fallback, pipx/uv rows with no version) never appears in `list`, even though scan tracked it in `software.json` | Either write every installed name into `versions.json` (with `versions: []`) or have `list` union `software.json` entries. The first keeps `list` fast and single-source; decide in OQ1 | done — every name written; version diff still ignores empty rows |
| 1.5 | **S** | `inventory.set_field` / `cmd_edit` | `--status` accepts any string; `vole edit x --status foo` writes an unknown status that only the next scan warns about | Validate `status ∈ STATUSES` at edit/add/restore time; return exit 2 | done — `edit --status` uses argparse choices (`add`/`restore` take no `--status`); `''` rejected too |
| 1.6 | **S** | `inventory.save` call sites | `OSError` from `save` (read-only dir, disk full, EPERM) is uncaught everywhere → Python traceback. `_load` handles read errors; writes do not | Wrap writes in one helper that prints `error: …` and exits 1, like `_load` | done — one `OSError` handler in `cli.main`; `save` removes its temp file on failure; moves out of `dropped.json` now write the destination first so a failed second write can't lose an entry |
| 1.7 | **S** | `signals/shell_history.py:23` | `datetime.date.fromtimestamp(int(...))` on a corrupt/huge timestamp raises `OverflowError`/`OSError`/`ValueError` and kills the whole scan | Catch and skip the line | done |
| 1.8 | **S** | `signals/config_refs.py:18` | Reads every top-level file in `~/.config/` fully into memory with no size cap, as text. A stray large/binary file makes scan slow or memory-heavy | Cap at e.g. 1 MiB per file; skip non-text by extension or NUL check | done — blanket `~/.config/*` scan replaced by an explicit list of files where a name means "wired in" (shell rc, fish config, git config, `mise/config.toml`) + 1 MiB cap; ignore lists, `starship.toml`, `.npmrc` dropped as coincidental matches; labels show the relative path |
| 1.9 | **S** | `sources/brew.py:50` | `brew leaves` hides formulae the user installed on purpose that are *also* a dependency of something else (common: `jq`, `python@3.x`, `openssl`) | Use `brew leaves --installed-on-request` (Homebrew ≥ 4) with fallback to plain `leaves` | done — suggested flag was wrong (`leaves -r` is a *subset* of leaves). Now `brew leaves` ∪ `brew list --formula --installed-on-request`, deduped by short name; old brews fall back to leaves only |
| 1.10 | **N** | `audit.py:49` | `cutoff = today − months×30 days` — approximate month; fine, but document that `--months 6` ≈ 180 days | | won't fix |
| 1.11 | **N** | `sources/apps.py` | Only top-level `/Applications/*.app`; `/Applications/Utilities/*.app` and nested vendor folders (Adobe, Microsoft) are skipped | Add one level of recursion or an allow-list of subfolders | done — one level down via shared `apps.app_bundles` (also used by spotlight); skips bundles inside `.app` and browser web-app folders `* Apps.localized` |
| 1.12 | **N** | `signals/shell_history.py` | zsh only. bash (`~/.bash_history`, no timestamps unless `HISTTIMEFORMAT`) and fish (`~/.local/share/fish/fish_history`) users get no history signal | Add fish (has timestamps) at least; document bash limitation | done — fish read from `~/.local/share/fish/fish_history`; newest date wins across shells; bash limitation noted in the module docstring |
| 1.13 | **N** | `inventory.py FORMAT = 1` | Any future field change means a format bump and hard refusal of existing files. Policy is intentional but undocumented | One paragraph in an ADR (see 1.2): additive fields never bump; renames/removals bump and ship a one-shot migration | done — [ADR-008](../../docs/adr/adr-008-inventory-format-versioning.md) (Proposed) |
| 1.14 | **N** | `audit.run` | `versions.json` is rewritten on every scan even when unchanged (same bytes, new mtime) | Compare rendered text before `os.replace`; skip write if identical. Also matters for `software.json` when no stubs were added (already skipped) | done — inside `inventory.save`, so every writer skips identical rewrites |

### 2. Security / privacy

Nothing exfiltrates data; all `subprocess.run` calls use list args without `shell=True`. Items are
hygiene and transparency.

| # | Sev | Where | Finding | Suggested fix | Status |
|---|-----|-------|---------|---------------|--------|
| 2.1 | **B** | `README.md` | Scan reads `~/.zsh_history`, `~/Library/*` mtimes, the `config_refs.CONFIG_FILES` list (shell rc, git config, mise config), and runs `brew`/`npm`/`mdls`. Users should be told what is read and that nothing leaves the machine or is stored except command *names* | Add a short **Privacy** section to README | done |
| 2.2 | **S** | `install.sh` | `curl … | sh` from `main` with no checksum or tag. Accepted industry pattern, but once the Homebrew tap exists (sha256-pinned, tagged) README should list brew first and curl as fallback | Reorder README Install once `homebrew-formula` ships | deferred — follows Homebrew |
| 2.3 | **S** | `install.sh:74` | `rm -rf "$LIB_DIR/vole"` with `LIB_DIR` from `$VOLE_INSTALL_LIB`. Safe for defaults; a weird override (`VOLE_INSTALL_LIB=/`) would `rm -rf //vole`. Low risk but cheap to guard | Refuse `LIB_DIR` that is `/`, `$HOME`, or not under `$HOME` unless `VOLE_INSTALL_FORCE=1` | done — also refuses relative paths and `.`/`..` segments; trailing slashes normalised. Covered by `tests/test_install.py` (offline; download path untested) |
| 2.4 | **S** | `inventory.save` | Data files created with default umask (typically 0644). `software.json` holds personal reasoning (employer, projects) | `os.open(..., 0o600)` for the temp file, or `chmod 600` after `os.replace`; make the data dir 0700 in `ensure_data_dir` | done — files 0600 on every save (also tightened when content is unchanged; leftover temp file mode not inherited); new data dir 0700, existing dirs keep their mode |
| 2.5 | **N** | `signals/config_refs.py` | Reads `~/.npmrc` (can contain auth tokens) into memory. Only regex-searched, never persisted — acceptable, but the file list should be reviewed consciously | Keep; mention in Privacy section. Consider dropping `.npmrc` from `CONFIG_FILES` since package names rarely appear there | done — `.npmrc` dropped with 1.8 |

### 3. Scalability / structure

| # | Sev | Where | Finding | Suggested fix | Status |
|---|-----|-------|---------|---------------|--------|
| 3.1 | **S** | `sources/__init__.py discover_all` | Registry dispatches by **identity** (`if discover is apps.discover … elif is pipx … elif is uv_tool … elif is bins`). Every source with cross-source state (owned apps, claimed shims) needs an edit here. Contradicts `base.py`'s "a source is any callable" and ADR-006 | Pass one `ScanContext` to every source (`ctx.home`, `ctx.cask_owned_apps`, `ctx.claimed_bins: set`). pipx/uv add to `ctx.claimed_bins`; bins reads it. Registry becomes a plain loop again | done — every source is `discover(ctx)`; brew publishes cask-owned apps, pipx/uv publish claimed bins; registry order documented |
| 3.2 | **S** | `signals/spotlight.py` | One `mdls` subprocess **per `.app`** (100+ apps → 100+ processes, several seconds), then an O(apps × casks) Caskroom glob inside the loop | `mdls` accepts many paths in one call; run once per `/Applications` dir and parse. Build the cask→app map once (reuse `brew.cask_owned_apps` data) | done — one `mdls` call per 200 apps (NUL-separated output, per-app fallback if garbled); one Caskroom walk via `brew.cask_apps`. 61 apps: 2.3 s → 0.1 s, identical dates |
| 3.3 | **S** | `audit.run` | 150-line function doing load → shape-check → discover → classify → write → print. The **classification logic (new/gone/todo/stale/pinned/resurrected) has zero tests** — it is the core product and only exercised manually | Split into `classify(entries, archived, installed, facts, cutoff) -> Report` (pure, testable) and `render(report)`. Add unit tests with fixture dicts; no subprocess needed | done — `classify` (pure) → `Report`, `render` → text, `run` does I/O only. Report output byte-identical before/after on 6 golden scenarios; 9 new unit tests |
| 3.4 | **S** | `cli.py` | 411 lines; three near-identical "move dropped → software" blocks (`edit --status active`, `restore`, `add`-on-archived), two identical confirm prompts (`delete`, `reset`), and `_print_entry` repeated with different headers | Add `inventory.archive(name)`, `inventory.restore(name, fields)` returning the saved entry, and a `_confirm(prompt, force)` helper. Target ≈ 250 lines | done — one `inventory.move()` (destination written first) backs archive and restore; cli loads both files through a small `_Inventory` holder, and `_confirm`, `_no_entry` and `_apply` replace the copied blocks. Output verified byte-identical over 34 commands. 419 → 394 lines: the ≈ 250 target was wrong, since the parser and the `list` table hold no duplication |
| 3.5 | **N** | `signals/__init__.py`, `signals/*.collect(home, entries=None)` | Signal contract is inconsistent: `entries` is accepted by all four but used only by `config_refs`; `app_state` returns a map keyed by *normalised* names that the registry must special-case via `lookup` | Same `ScanContext` idea as 3.1; or make every signal return facts keyed by entry name and move normalisation into `app_state.collect` | done — every signal is `collect(ctx)`; `ctx.entries` carries the name list; app_state / shell basename resolution live inside those signals; `collect_all` is a plain loop over `SIGNALS` |
| 3.6 | **N** | `signals/app_state.lookup` | Substring scan over all keys for every entry (O(entries × keys), `len(k) > 4` guard). Fine at hundreds; will crawl at thousands of Library entries | Pre-index keys by prefix, or accept and note | done — `_gram_index` maps each 5-gram of Library keys → candidates; `lookup` filters those instead of scanning every key. Same answers as the full scan (tested) |
| 3.7 | **N** | `sources/cargo.py discover` | Three separate fall-through branches to `_from_bin_dir` | One `try/except` + `if returncode == 0` then a single fallback | done — one success path, one `_from_bin_dir` fallback |
| 3.8 | **N** | `tests/` | All CLI tests spawn `python -m vole` subprocesses (fine, ~1 s). No tests for `brew`, `apps`, `mise`, `npm`, `spotlight`, `app_state`, `config_refs`, or `audit.run`. Sources with parsers (`cargo`, `pipx`, `uv`, `yarn`, `pnpm`, `asdf`) are the only well-covered ones | Add parser-level tests for `brew._version_map`, `mise`, `npm`; fixture-dir tests for `app_state` and `config_refs`; see 3.3 for audit | done — Tier A only: `_version_map`, `mise.parse_ls`, `npm_global.parse_ls_json` (+ missing-tool empty). brew/apps/spotlight/app_state/config_refs/classify already covered by 3.1–3.6; deeper `audit.run` / live tests skipped |

### 4. Dead code / hygiene

| # | Sev | Where | Finding | Status |
|---|-----|-------|---------|--------|
| 4.1 | **B** | git index | **20 files tracked as `100755`** including `README.md`, `CHANGELOG.md`, `AGENTS.md`, every `dev/*.md`, `docs/adr/*.md`, `vole/cli.py`, `tests/test_audit.py`. GitHub shows an "executable" badge; packaging tools may warn. Only `bin/vole` and `install.sh` should be executable. Also several dirs are `0700` locally (harmless in git) | done — cleared `+x` on 18 tracked files; only `bin/vole` and `install.sh` remain `100755` |
| 4.2 | **S** | `signals/__init__.py:6` | `SignalMap` imported, unused | done — gone with 3.5 rewrite |
| 4.3 | **S** | `signals/spotlight.py:2` | `os` imported, unused | done |
| 4.4 | **S** | `sources/brew.py:6` | `List` imported, unused | done — `List` is used by `formula_names` (landed with 1.9) |
| 4.5 | **S** | `versions.py:2` | `Tuple` imported, unused | done — dropped unused import |
| 4.6 | **S** | `cli.py:107` | `__import__('collections').Counter(...)` — import `collections` at the top like `audit.py` does | done — top-level `import collections` |
| 4.7 | **S** | `cli.py cmd_delete` | `where` assigned, never read | done (with 3.4) — `where` now picks the file |
| 4.8 | **S** | `paths.py:5` | `DATA_FILES` tuple defined, never used (`inventory_paths` hardcodes the three) | done — `inventory_paths` builds from `DATA_FILES` |
| 4.9 | **N** | `sources/apps.py:20` | `owned=None` fallback calls `cask_owned_apps()` again; `discover_all` always passes it. Keep for standalone use or drop the fallback — pick one | done — gone with 3.1 (apps reads `ctx.cask_owned_apps`) |
| 4.10 | **N** | `dev/STATUS.md` | Stale (still says `inventory-check` is a candidate; last updated 2026-10-11). Refresh at the same time as the changelog promotion | won't fix — working file, refresh whenever |
| 4.11 | **N** | three launchers | `bin/vole`, `vole/__main__.py`, and the one `install.sh` generates (soon a fourth from the brew formula). All trivial; just make sure the brew formula reuses `python3 -m vole` semantics rather than a fifth variant | deferred — note on `homebrew-formula`; existing launchers all call `vole.cli.main` |

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | `list` omits unversioned installs (1.4): write every installed name to `versions.json` with `versions: []`, or make `list` union `software.json`? | locked | **Write every installed name** (empty list allowed). `versions.json` then truly means "what scan saw"; `list` stays one read. Shape check already allows empty lists |
| 2 | ADRs (1.2): write the seven files now, or trim the index to README/TEMPLATE and add them later? | locked | **Remove the links.** Index emptied; durable docs no longer reference ADR files. Task docs keep "ADR-00X" as plain historical text |
| 3 | Scope of the structural refactors (3.1, 3.3, 3.4) — before `v0.1.0` or right after? | locked | **Before the tag.** 3.1, 3.3 and 3.4 all landed before `v0.1.0`, with no user-visible change |
| 4 | File permissions on data (2.4): enforce `0600` / `0700`? | locked | **Yes** |
| 5 | Drop `.npmrc` from `config_refs` (2.5)? | locked | **Dropped**, together with ignore lists and `starship.toml` — coincidental matches only |

## Non-goals

- No new sources or signals.
- No CLI surface changes beyond `--version` and `status` validation.
- No format bump.

## Done when

- [x] All **B** items fixed: Caskroom prefix, ADR links, `--version`, Privacy section, exec bits.
- [x] All **S** items fixed or deferred with a reason (2.2 → Homebrew README reorder).
- [x] **N** items fixed, won't-fix, or deferred (4.11 → Homebrew launcher; 1.10 / 4.10 won't fix).
- [x] `audit` classification has unit tests (3.3).
- [x] Tests green on `/usr/bin/python3` (3.9) and current Homebrew Python.
- [x] `dev/STATUS.md` refreshed; version/`CHANGELOG` set to `0.1.0`. Tag + `homebrew-formula` are the next human steps (task docs not deleted).

## Notes

Commands used for the review (reproducible):

```sh
python3 -m unittest discover -s tests            # 62 tests OK
/usr/bin/python3 -m unittest discover -s tests   # 3.9 floor OK
git ls-files -s | awk '$1=="100755"{print $4}'   # exec-bit audit
rg -n "Caskroom|__import__|entries=None" vole
```

Static-check note: no `pyflakes`/`flake8` in the environment; unused imports were found with a
small `ast` walk. Worth adding `python3 -m pyflakes vole tests` to `dev/README.md` as an
optional local check (still zero *runtime* dependencies).
