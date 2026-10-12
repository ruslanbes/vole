# Source: SDKMAN!

- **Task ID:** `source-sdkman`
- **Status:** backlog
- **Related:** `mise`, `asdf` (other multi-version runtime managers); JVM niche (Java, Groovy, Kotlin, …)

## Problem

SDKMAN! (`sdk`) is the common way to install and switch JVM-language SDKs on a Mac —
Java, Groovy, Kotlin, Scala, Gradle, Maven, and friends. Those installs live under
`~/.sdkman/candidates/` and do not show up via brew, mise, or asdf unless the user
also registered them there. vole currently has no visibility into them.

## Goal

`vole scan` lists SDKMAN!-managed candidates under source id `sdkman`, with one entry
per candidate name and every installed version in `versions`.

## Open questions

Do not implement while any row is `open`.

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Discovery — walk `~/.sdkman/candidates/` or call `sdk`? | open | **Proposal:** walk `home / '.sdkman' / 'candidates' / <name> / <version>` (skip the `current` symlink). No `sdk` on PATH required; works with `VOLE_DATA_DIR` / fake homes in tests. Fallback to no-op when the tree is missing |
| 2 | Entry shape — one row per candidate, multi `versions`? | open | **Proposal:** same as mise/asdf — name = candidate (`java`, `kotlin`, `groovy`, …), `versions` = installed ids (e.g. `21.0.4-tem`, `17.0.12-amzn`) |
| 3 | Include every candidate SDKMAN knows, or only JVM languages? | open | **Proposal:** **every** installed candidate under `candidates/` (Gradle/Maven/Scala too). Restricting to Java/Groovy/Kotlin would hide real installs for little gain |
| 4 | Registry order vs mise/asdf when the same name clashes? | open | **Proposal:** after `asdf` (mise → asdf → sdkman → ollama). First-wins keeps mise/asdf ownership when both manage e.g. `java` |
| 5 | Source id string? | open | **Proposal:** `sdkman` |

## Non-goals

- Not calling `sdk install` / `sdk uninstall` or changing the active `current` symlink.
- Not reading project-local `.sdkmanrc` files (inventory is machine-global, like other sources).
- Not inventoring SDKMAN! itself as a candidate.

## Done when

- [ ] Scan lists SDKMAN! candidates/versions when `~/.sdkman/candidates` exists.
- [ ] Missing SDKMAN! tree → empty, no error.
- [ ] First-wins vs mise/asdf documented by registry order.
- [ ] Parser/fixture tests + README sources list updated.

## Notes

Typical layout:

```
~/.sdkman/candidates/
  java/
    17.0.12-amzn/
    21.0.4-tem/
    current -> 21.0.4-tem
  kotlin/
    2.0.20/
    current -> 2.0.20
  groovy/
    4.0.22/
    current -> 4.0.22
```

`current` is a symlink to the active version — skip it when collecting version dirs.
Candidate names are the directory names under `candidates/`.
