# Privacy

To find out what is installed and when it was last used, `vole scan` reads:

* App bundles in `/Applications` and `~/Applications`, and the Homebrew Caskroom
* Steam library folders and `appmanifest_*.acf` under `~/Library/Application Support/Steam` (names and build ids only)
* Package-manager listings, if the tool is installed: `brew`, `cargo`, `pipx`, `uv`, `npm`, `yarn`, `pnpm`, `mise`, `asdf`, plus `go version -m` on files in `~/go/bin`
* File names in `~/.local/bin`, `~/.cargo/bin` and `~/.ollama/models`
* Shell history: `~/.zsh_history`, fish history, and `~/.bash_history`, for command names and dates (zsh/fish use real timestamps; untimestamped bash/zsh lines use a bounded guess from the history file’s mtime — approximate)
* Spotlight "last used" dates for apps
* Modification times of folders in `~/Library` (Application Support, Containers, Preferences, Saved Application State). Names and dates only, never their contents
* Shell, git and mise config files (`.zshrc`, `.zprofile`, `.bash_profile`, fish `config.fish`, `.gitconfig`, `~/.config/git/config`, `~/.config/mise/config.toml`), searched for tool names

What it saves, in `~/.config/vole/`: software names, where each came from, installed versions, the
date vole first saw each one, a `last_used` date (newest dated usage signal seen so far — advanced
only when a newer signal appears), and the `why` / `keep` notes you write. History lines and config
contents are only used during a scan and are never saved.
