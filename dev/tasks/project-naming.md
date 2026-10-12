# Pick a project name

- **Task ID:** `project-naming`
- **Status:** done

## Problem

The repo is called `software-tracker`, which is descriptive and forgettable. It is also the
generic term for a whole category, so it is unsearchable and almost certainly taken. A name is
needed before the first public commit, because renaming after people have cloned or starred it
is a cost that compounds.

The tool will reference [Mole](https://github.com/tw93/Mole) in its docs as a complementary
tool — Mole cleans and uninstalls, this records *why* things are installed. A name that nods to
that pairing is a bonus, not a requirement.

## Goal

One name that works as a repo name and a CLI command. Homebrew formula packaging is a
separate task (`homebrew-formula`).

## Candidates

### General

| Name | For | Against |
|------|-----|---------|
| **provenance** | Exactly the concept: where a thing came from and on whose authority. Reads well in prose — "check the provenance of your Mac" | Long for a CLI (10 chars); a common word, so likely taken somewhere |
| **stocktake** | Plain, concrete, and what the tool literally does. Uncommon as a project name | British-English flavoured; says *what* without saying *why* |

### Rhyming with Mole

| Name | For | Against |
|------|-----|---------|
| **vole** | A mole's smaller cousin — the pairing tells the story by itself: Mole digs things out, Vole remembers why they were there. Four letters, trivial to type, no shell collision | Only works as a joke if the reader knows Mole |
| **knoll** | What a molehill is. Short, memorable, pleasingly odd as a command | The connection needs explaining; easy to misspell as "noll"/"nol" |

### Unusual and catchy

| Name | For | Against |
|------|-----|---------|
| **alibi** | Every installed tool needs an alibi. Maps precisely onto the one question the tool asks, and is memorable on first hearing | Slightly cute; "alibi" has crime connotations that may read oddly in a work context |
| **receipts** | "Keep the receipts" — current idiom for *being able to justify yourself*. Says both the record and the justification in one word | Plural reads awkwardly as a command (`receipts --list`); overloaded in finance tooling |

## Open questions

Do not rename while any row is `open`.

| # | Topic | Status | Decision |
|---|-------|--------|----------|
| 1 | Which name? | locked | **vole** — Mole pairing is part of the framing (Mole digs things out; Vole remembers why they were there) |
| 2 | Is it free as a GitHub repo / Homebrew formula / `brew install` name? | locked | GitHub: taken — [ruslanbes/vole](https://github.com/ruslanbes/vole). Homebrew: deferred to `homebrew-formula` |
| 3 | Does the name need to survive the tool growing beyond macOS? `vole`/`alibi` are neutral; `stocktake` is too | locked | Yes — and vole is platform-neutral |

## Non-goals

- Not a logo or visual identity.
- Not a domain purchase.

## Done when

- [x] A name is chosen; public GitHub repo exists (`ruslanbes/vole`).
- [x] The repo directory, `README.md` title, and in-code references say `vole` (CLI package, `bin/vole`).
- [x] The rejected candidates stay in this doc, so the next person does not re-propose them.

## Notes

Shortlist bias worth naming: **vole** is the strongest if the Mole pairing is going to be a
real part of how this is presented, and the weakest if it is not. Decide that framing first and
the name follows.
