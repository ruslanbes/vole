# Privacy

To find out what is installed and when it was last used, `vole scan` reads:

* App bundles in `/Applications` and `~/Applications`, and the Homebrew Caskroom
* Package-manager listings, if the tool is installed: `brew`, `cargo`, `pipx`, `uv`, `npm`, `yarn`, `pnpm`, `mise`, `asdf`, plus `go version -m` on files in `~/go/bin`
* File names in `~/.local/bin`, `~/.cargo/bin` and `~/.ollama/models`
* Shell history: `~/.zsh_history` and fish history, for command names and dates
* Spotlight "last used" dates for apps
* Modification times of folders in `~/Library` (Application Support, Containers, Preferences, Saved Application State). Names and dates only, never their contents
* Shell, git and mise config files (`.zshrc`, `.zprofile`, `.bash_profile`, fish `config.fish`, `.gitconfig`, `~/.config/git/config`, `~/.config/mise/config.toml`), searched for tool names

What it saves, in `~/.config/vole/`: software names, where each came from, installed versions, the
date vole first saw each one, and the `why` / `keep` notes you write. History lines, usage dates and config contents are only used for the report you see and are never saved.