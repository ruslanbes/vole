# Source: IntelliJ-downloaded JDKs

- **Task ID:** `source-intellij-jdks`
- **Status:** backlog
- **Related:** `source-sdkman` (parallel JVM install path); not the same tree

## Problem

IntelliJ IDEA can **Download JDK** from Project Structure without SDKMAN, Homebrew, or a
system installer. Those JDKs live under a JetBrains/user path (commonly
`~/Library/Java/JavaVirtualMachines/` on Mac, sometimes an IDE `.jdks` folder) and are
invisible to vole’s current sources. Users who only ever install Java from the IDE get no
inventory row and no drop-candidate signal for unused JDKs.

## Goal

`vole scan` lists JDKs installed by IntelliJ’s built-in downloader under a dedicated source
id, with versions, so they can be reasoned about like any other install.

## Open questions

Do not implement while any row is `open`.

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Which directories to scan? | open | **Proposal:** `home / 'Library' / 'Java' / 'JavaVirtualMachines'` first (documented IntelliJ download location on Mac). Confirm whether current IDEA also writes under `~/.jdks` or inside the Application Support JetBrains tree and include those if still used |
| 2 | How to name entries and versions? | open | **Proposal:** one row per JDK home dir under that folder (folder name is usually vendor+version, e.g. `temurin-21.0.4`). `versions` = best-effort from dir name or `release`/`Contents/Home` metadata; source id `intellij-jdk` |
| 3 | Dedup vs SDKMAN / brew / `/Library/Java/JavaVirtualMachines`? | open | **Proposal:** first-wins. Register after brew/apps so a brew cask or system JVM that shadows the same logical name keeps brew; IntelliJ-only downloads still appear. Do **not** walk system `/Library/Java/JavaVirtualMachines` in this source (different installer story — optional later task) |
| 4 | JetBrains Runtime (JBR) bundled inside the `.app`? | open | **Proposal:** **skip** — that is part of the IDE app bundle, already covered (or skipped) by the `app` source. This task is only for JDKs the user downloaded for projects |
| 5 | Android SDK / other non-JDK “SDKs” in IDEA? | open | **Proposal:** **out of scope** — separate task if needed |

## Non-goals

- Not parsing `.idea` / `misc.xml` project SDK pointers (machine inventory, not per-repo).
- Not calling into the IDE or reading JetBrains account/license state.
- Not replacing `source-sdkman`; both trees can coexist on one Mac.

## Done when

- [ ] Scan lists IntelliJ-downloaded JDKs when the user Library JVMs tree exists.
- [ ] Missing tree → empty, no error.
- [ ] Bundled JBR inside IntelliJ.app is not double-counted by this source.
- [ ] Fixture tests + README sources list updated.

## Notes

- IDEA **Download JDK** ≠ SDKMAN. SDKMAN uses `~/.sdkman/candidates/`; IDEA uses its own cache (see [Stack Overflow: where IntelliJ stores downloaded JDKs](https://stackoverflow.com/questions/71669393/where-does-intellij-store-the-jdks-that-it-downloads-on-my-behalf)).
- Official docs: [SDKs | IntelliJ IDEA](https://www.jetbrains.com/help/idea/sdk.html) — Download JDK vs Add JDK from disk.
- Typical Mac layout to verify on a real machine before locking OQ1:

```
~/Library/Java/JavaVirtualMachines/
  temurin-17.0.12/
  temurin-21.0.4/
  ...
```

Each entry is often a dir that contains `Contents/Home` (macOS JDK layout) or is itself a JDK home.
