# vole

Answers one question for everything installed on this Mac: **why is this here?**

```text
$ vole scan
tracked: 142   installed: 138

MISSING A REASON (3):
  ffmpeg
  qwen3-coder:30b
  parsec

DROP CANDIDATES (2):
  ratatui                      0.22.2     cargo          no signal since 2025-11-02 (shell 2025-11-02)
  Sketch                       100.3      app            no usage signal at all — needs a manual look

VERSIONS (1 changed since last scan):
  jq                                 1.7.1  ->  1.8.1
```

```text
$ vole list brew
NAME          VERSION   SOURCE         STATUS   KEEP         WHY
ffmpeg        7.1.1     brew-formula   active   -            TODO
imagemagick   7.1.2-27  brew-formula   active   dependency   used in photo editors
jq            1.8.1     brew-formula   active   -            parse json in shell

3 installed  |  3 brew-formula  |  1 kept, 1 without a reason
```

## Why bother

Installing new software on Mac is easy, but eventually you end up with your system filled with software that you tried once and don't use anymore. Things get twice as bad for software engineers who additionally install helper shell tools, SDKs, linters and so on.

[vole](https://github.com/ruslanbes/vole) helps you to audit your software. It scans everything that is installed on your Mac and lets you record why is it installed.

Complementary to [Mole](https://github.com/tw93/Mole): Mole digs things out; Vole remembers
why they were there. Neither does the other's job.

## What it does / does not

**Does:** track brew formulae and casks, `/Applications`, `~/go/bin`, `~/.local/bin` and other sources.

**Does not:** uninstall or auto-update software. There are dedicated tools for that.

## Install

```sh
brew install ruslanbes/vole/vole
```

Or without Homebrew:

```sh
curl -fsSL https://raw.githubusercontent.com/ruslanbes/vole/main/install.sh | sh
```

Curl puts the CLI on `~/.local/bin` (add that directory to your `PATH` if needed). Needs
macOS with Command Line Tools `python3` 3.9+. Re-run anytime to refresh from `main`.

Or from a clone: `./install.sh`, or run `bin/vole` / `python3 -m vole` without installing.

## Use

```sh
vole                         # help
vole help                    # same
vole --version               # print version
vole scan                    # scan and save; creates ~/.config/vole/ on first run
vole scan --dry-run          # report only, never writes
vole list [filter]           # table of installed software: version + why
vole edit NAME --why "…"     # set why / keep / status (software or dropped)
vole drop NAME               # archive (alias for edit --status dropped)
vole add NAME --source …     # create, or restore from dropped and set fields
vole restore NAME            # move from dropped.json back to software.json
vole delete NAME             # permanently remove (asks first; --force to skip)
vole reset                   # delete all inventory data (asks first; --force to skip)
```

`vole scan` archives entries that are no longer installed (reason kept in `dropped.json`).
If that software comes back, scan restores it — unless you dropped it yourself with
`vole drop` (or `edit --status dropped`), which stays sticky while installed. Use
`vole restore NAME` to undo a sticky drop or a bad auto-archive. `edit` works on
archived rows too.

Examples:

```sh
vole edit jq --why "JSON in shell scripts"
vole edit imagemagick --keep dependency --why "thumbnails for the blog"
vole drop old-tool
vole restore old-tool
vole add manual-bin --source local-bin --why "helper script"
vole delete obsolete-thing --force
vole list brew
```

## Use with agents

Instead of editing each app per hand launch your local agent harness (Claude code,  Antigravity, Cursor etc.) and tell it about vole. It should learn the tool from the help command and help you auditing stuff. Sample prompts:

> Check the vole shell tool and learn how to use it

> Give your best guesses for the reasons for the tools that vole lists as "MISSING A REASON". Save those where
> you have high confidence.

> Use vole to mark all Microsoft Office products as kept because of the mdm

## Versions

Vole remembers installed version and tells if it changed:

```
VERSIONS (3 changed since last scan):
  jq                   1.7.1  ->  1.8.2
  ripgrep              + 15.2.0
  imagemagick          - gone (was 7.1.2-27)
```

It does not have an auto-updater for installed tools or check if there is a newer version online.

## Sources

Tracks software installed from:

* App Store (`/Applications`)
* Homebrew: casks and formulae
* Steam: games with an installed Steam appmanifest
* Cargo: crates installed with `cargo install`
* Go: global binaries installed with `go install`
* pipx: Python CLIs installed with `pipx install` (shims in `~/.local/bin` are not double-counted)
* uv: CLIs installed with `uv tool install` (same shim dedup; pipx wins on name clashes)
* Npm: global packages installed with `npm install -g`
* Yarn classic: global packages from `yarn global add` (npm wins on name clashes; Berry has no globals)
* pnpm: global packages installed with `pnpm add -g` (npm/yarn win on name clashes)
* Mise: any SDKs installed with [mise](https://mise.jdx.dev/)
* asdf: runtimes installed with [asdf](https://asdf-vm.com/) (mise wins if both claim a name)
* Ollama: any model pulled with `ollama pull`
* More to come...

## Keeping

Use `--keep` to mark an entry so that vole stops mentioning it as unused. Possible reasons:

* `mdm`: The software is controlled by the Mobile Device Management - usually on your corporate laptop. Even if you don't use it, you can't uninstall it on your own, so no reason to get signals about it.
* `dependency`: Something else needs it. Typical for things like `imagemagick`
* `in-use`: Vole could not find usage signals but you know you use it.
* Anything else — `--keep` is a free-form reason; these are just examples. 

## Known rough edges

- Homebrew casks that install a `.pkg` rather than a `.app` can appear twice — once as the cask and once
  as the app. Drop one of the two with `vole drop NAME`.
- App names and cask names differ often enough that some manual merging is unavoidable.

## Privacy

Everything stays on your Mac. vole makes no network requests (only `install.sh` downloads vole itself).

See more in [PRIVACY.md](PRIVACY.md).