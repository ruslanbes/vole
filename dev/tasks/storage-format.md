# Choose the inventory storage format

- **Task ID:** `storage-format`
- **Status:** done — JSON chosen 2026-10-09; implementation and remaining questions moved to `switch-to-json`
- **Parent / blocked by:** feeds `python-only-restructure`; would supersede ADR-003

## Problem

The inventory is TOML only because it started as a hand-edited file. The direction now is that
users edit through `vole` commands, not by opening the file. That removes the main reason for
TOML, and TOML is the hardest format to support on the 3.9 floor: no stdlib reader before 3.11
and no stdlib writer at all. That is why the tool carries a regex parser and the raw-text-block
rules in ADR-003.

## Goal

Pick the format that is easiest to store correctly with the stdlib on Python 3.9, while keeping
what still matters: git-diffable history, a file a human can read on GitHub, and data that
cannot be silently corrupted.

## What the data looks like (measured 2026-10-09)

| File | Entries | Size | Notes |
|------|---------|------|-------|
| `software.toml` | 79 | 13 KB | hand-written reasons |
| `dropped.toml` | 70 | 13 KB | hand-written reasons |
| `versions.toml` | 78 | 6 KB | machine-written |

- Fields: `source`, `why`, `projects` (list), `added`, `status`, plus optional `keep` (27) and `note` (8).
  Longest `why`/`note` is ~300 characters.
- **No comments inside entries, no inline comments.** Only a file header. Migrating loses no
  hand-written content.
- Small: a full rewrite on every change is trivially cheap.

## What still matters if nobody edits by hand

| Criterion | Why it matters |
|-----------|----------------|
| Stdlib read **and** write on 3.9 | ADR-004: zero deps, CLT Python |
| Stable, line-oriented diffs | `versions` history is read through `git diff`; reasons should be too |
| Readable without the tool | Recovery, GitHub browsing, an agent reading it |
| Safe writes | Inventory took months to write; atomic replace stays mandatory |
| Lists and optional fields | `projects`, `versions`, missing `keep`/`note` |
| Low code to maintain | Fewer rules like "quote keys", "never split on commas" |

Comments stop mattering: the header explanation can live in the README, or as a `"_comment"`
field if wanted.

## Candidates

| Format | Stdlib 3.9 | Read on GitHub | Diffs | Lists | Code we own | Verdict |
|--------|-----------|----------------|-------|-------|-------------|---------|
| **TOML** (today) | No reader, no writer | Good | Good | Yes | Regex parser + raw-block editing + key quoting | Hardest to keep correct |
| **JSON**, pretty-printed | `json` | Good | Good if output is deterministic | Yes | ~10 lines | **Recommended** |
| **JSONC** | No (comments need a custom stripper) | Good | Same as JSON | Yes | Comment stripper; comments lost on rewrite anyway | Pays for comments nobody writes |
| **JSON Lines** (one entry per line) | `json` | OK | Excellent: one entry = one line | Yes | ~10 lines | Good runner-up; long lines read poorly |
| **SQLite** | `sqlite3` | No (binary) | None | Via tables / JSON column | Schema + migrations | Overkill; kills git history |
| **plist** (XML) | `plistlib` | Verbose | Noisy | Yes | ~10 lines | Mac-native but unpleasant to read |
| **INI** | `configparser` | Good | Good | No native lists | List encoding | Loses on lists |
| **CSV / TSV** | `csv` | Good as a table | Good | No native lists | List + escaping rules | Same; and `why` has commas |
| **YAML** | No | Good | Good | Yes | Needs PyYAML | Violates ADR-004 |

### Notes per option

**JSON (pretty-printed, deterministic).** Write with `sort_keys=True, indent=2,
ensure_ascii=False` and a trailing newline. Then every write of the same data is
byte-identical, and changing one field changes one line in `git diff`. Names like `zoom.us`,
`azure/kubelogin/kubelogin` or `Microsoft Excel` are just string keys, so bugs 1 and 2 in
`architecture-review` (key quoting, comma-splitting) become impossible rather than guarded
against. `jq` works on it for free. The only diff wart: adding a key after the last one also
touches the previous line's comma.

**JSONC.** Its one feature, comments, is exactly what the CLI-only direction removes. A tool
that rewrites the file through `json.dumps` drops comments anyway, so keeping them would mean
going back to raw-text editing. Not worth it.

**JSON Lines.** Best possible diffs and trivially append-friendly. But a 300-character `why`
plus `note` on one line is hard to read on GitHub, and the file is not valid JSON as a whole,
so `jq` needs `-s` or line mode. Choose it only if diff granularity beats readability.

**SQLite.** Real transactions and queries, all stdlib. But a binary file ends the "commit the
inventory and read its git diff" workflow the README recommends for `versions`, and hand
recovery needs the `sqlite3` CLI. The data is far too small to need it.

**plist.** Native to macOS (`plutil -p` reads it), stdlib on every version. XML makes each entry
about three times longer, and diffs are full of `<key>`/`<string>` noise.

## Suggested shape (JSON)

```json
{
  "format": 1,
  "apps": {
    "azure/kubelogin/kubelogin": {
      "added": "2026-09-13",
      "keep": "dependency",
      "note": "tapped formula: `brew leaves` prints the full name",
      "projects": ["work/platform"],
      "source": "brew-formula",
      "status": "active",
      "why": "kubectl auth for the AKS clusters"
    }
  }
}
```

- `format` makes later migrations explicit.
- Keep the three files separate: `versions` churns on every upgrade and would bury reason changes
  in the same diff — that argument from the README still holds.
- Optional fields are absent, never `null`, so diffs stay quiet.

## What changes if we switch

- **ADR-003 is superseded.** The rules it carries (quote keys, never split on commas, raw blocks)
  exist only because of TOML. What survives is "one writer, sorted, atomic replace".
- **The CLI must cover every edit people made by hand:** add, edit any field, remove a field,
  drop, un-drop, rename an entry. Today `edit` covers five fields; adding and dropping are manual.
- **Migration** is a one-time `vole migrate` that reads the old TOML with the existing regex
  parser (works on 3.9) and writes JSON. Old files are kept as `.bak`.
- `inventory-check` shrinks to "does `json.load` succeed and does it match the shape", and works
  on 3.9 with no `tomllib` caveat.
- README "Entry format" and "Quote any name" sections go away; replaced by the CLI reference.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Which format? | locked | **Pretty-printed JSON** |
| 2–4 | Files, location, TOML support | moved | Open questions 2–4 in `switch-to-json` |

## Non-goals

- No implementation in this task — a decision, an ADR, and follow-up tasks.
- Not a database or sync service.

## Done when

- [ ] Format chosen; new ADR written, ADR-003 marked Superseded.
- [ ] CLI coverage gap (add / drop / rename / remove field) is a backlog task.
- [ ] Migration is a backlog task (or folded into `python-only-restructure`).
