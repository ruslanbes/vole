# Read the whole repo as a stranger before publishing

- **Task ID:** `first-public-pass`
- **Status:** done
- **Parent / blocked by:** <!-- project-naming done; questions locked -->

## Problem

The tool grew inside one person's work repo, and the documentation still shows it. It names that
person's software, assumes their machine, and quotes numbers only true of their install. A reader
arriving from GitHub has none of that context, and some of it should not be public at all.

## Goal

Every file reads as written for a stranger, with no private detail and no claim the project
cannot back up.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Keep the real examples (`azure/kubelogin/kubelogin`, Intune-managed apps) as realistic illustrations, or replace with invented ones? | locked | **Keep real examples.** Author reviews them before publishing |
| 2 | Does the README describe the tool, or also argue for the practice of recording *why* software is installed? | locked | **Argue for the practice** — README is more than a man page |

## Non-goals

- Not a rewrite of the tool. Documentation and framing only.
- Not marketing copy.

## Implementation

Known residue, found by reading the README on 2026-10-06:

- **"Known rough edges"** names specific private software: Foxit, Telegram, Slack, Windows App,
  Citrix. The underlying points are general (pkg casks list twice; MDM-delivered apps also exist
  as casks) — keep the points, lose the inventory.
- **"Items in the Brewfile but not yet installed show as no longer installed. Expected while the
  target machine is still being built."** This describes one machine migration in 2026 and means
  nothing to anyone else.
- **"A tracker that only reads the Brewfile misses ~17 tools — that gap is what prompted this."**
  A number from one machine, stated as a general fact.
- **`EXTENDED_HISTORY` was set in `~/.zshrc` on 2026-09-13**, cited as though the reader shares
  that history. The point to keep: the shell-history signal only sees as far back as timestamps
  go, so it is worthless on day one and improves monthly.
- Check every remaining date and count for the same problem.

Then the wider pass:

- Does `python3 -m vole` work from a clean clone with an empty `~/.config/vole/`? That is the
  first thing anyone runs (after clone).
- README should open with the problem and the practice, then what vole does / does not do, then
  install. Not install-first.
- Mole relationship is already stated once in the intro — keep a single early mention.
- Every claim tested or softened. Python floor is already **3.9+** in the README; confirm tests
  still pass under `/usr/bin/python3`.
- Real examples stay (OQ1); scrub only the private rough-edge inventory and machine-only numbers
  listed above. Author does a final example review before publish.

## Done when

- [x] No private software names, machine-specific numbers, or dates presented as general facts
      (except deliberate real examples the author has reviewed).
- [x] A clean clone runs without errors and the README's first commands work verbatim.
- [x] The README argues for recording *why* software is installed, then describes the tool.
- [x] The Mole relationship is stated once, early.
- [x] Every claim is either tested or softened.

## Notes

Name is **vole** (`project-naming` done). Questions locked 2026-10-09.
