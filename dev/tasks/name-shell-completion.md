# Shell autocomplete for entry names

- **Task ID:** `name-shell-completion`
- **Status:** backlog
- **Related:** `name-case-insensitive`, `name-fuzzy-match`, `name-glob`; brew / `install.sh`

## Problem

Typing `Google Chrome` (with quotes) is slow and typo-prone. Interactive users expect
Tab completion of known inventory names (and subcommands) the way `git` / `brew` do.

Completion does not help non-interactive agents as much as fuzzy/glob, but it is the
best UX for humans at a terminal.

## Goal

Ship shell completion that at least completes:

- Subcommands (`scan`, `why`, `keep`, `drop`, …).
- Entry names from `software.json` ∪ `dropped.json` (and ideally `versions.json` where
  relevant) for name-taking verbs.

Support **zsh** first (default on modern macOS); bash and/or fish as follow-ups (OQ).

Install path: document how brew and curl installs enable completion (copy script or
`COMPLETIONS` dir).

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Which shells in v1? | open | **Proposal:** zsh only first; bash second; fish later |
| 2 | Dynamic vs static script? | open | **Proposal:** completion calls `vole` (or reads JSON) for live names — stale static lists are worse |
| 3 | Quote insertion for names with spaces? | open | Completer should insert properly quoted / escaped names |
| 4 | Brew formula hook? | open | Tap formula installs completion into Homebrew’s completions dir when possible |
| 5 | Curl / `install.sh`? | open | Install zsh function under `~/.zsh/completions` or print enable instructions |
| 6 | Overlap with fuzzy? | open | Independent — completion prevents typos; fuzzy still helps when Tab isn’t used |

## Non-goals

- Not a TUI picker / fzf integration in v1.
- Not rewriting core name resolution (that’s the other name-* tasks).
- Not requiring a completion framework beyond what the shell already supports.

## Done when

- [ ] zsh completion for subcommands + entry names works after documented install steps.
- [ ] Names with spaces complete to a form the shell accepts without manual quoting gymnastics.
- [ ] README Install documents enabling completion; brew path covered if tap is in use.
