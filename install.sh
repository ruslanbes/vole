#!/bin/sh
# Install vole from GitHub main (or from a local checkout when run as ./install.sh).
#
#   curl -fsSL https://raw.githubusercontent.com/ruslanbes/vole/main/install.sh | sh
#
# Overrides (mainly for tests):
#   VOLE_INSTALL_LIB   where the package lands   (default: ~/.local/share/vole)
#   VOLE_INSTALL_BIN   where the `vole` launcher (default: ~/.local/bin)
#   VOLE_REPO          skip download; copy from this checkout directory
#   VOLE_INSTALL_FORCE=1  allow a VOLE_INSTALL_LIB outside $HOME (e.g. a temp dir)

set -eu

REPO_URL="https://github.com/ruslanbes/vole"
BRANCH="main"
TARBALL_URL="${REPO_URL}/archive/refs/heads/${BRANCH}.tar.gz"

LIB_DIR="${VOLE_INSTALL_LIB:-$HOME/.local/share/vole}"
BIN_DIR="${VOLE_INSTALL_BIN:-$HOME/.local/bin}"

die() { echo "install: $*" >&2; exit 1; }

# Root would put files in /var/root and a launcher that users never find.
if [ "$(id -u)" -eq 0 ]; then
  die "do not run as root — install for your user account (no sudo)"
fi

# LIB_DIR/vole is replaced with rm -rf below, so refuse paths where that could hurt.
while [ "${LIB_DIR%/}" != "$LIB_DIR" ]; do LIB_DIR=${LIB_DIR%/}; done
case "$LIB_DIR" in
  "") die "VOLE_INSTALL_LIB must not be / or empty" ;;
  /*) ;;
  *) die "VOLE_INSTALL_LIB must be an absolute path (got: $LIB_DIR)" ;;
esac
case "/$LIB_DIR/" in
  */../*|*/./*) die "VOLE_INSTALL_LIB must not contain . or .. (got: $LIB_DIR)" ;;
esac
[ "$LIB_DIR" != "${HOME%/}" ] || die "VOLE_INSTALL_LIB must not be your home directory"
case "$LIB_DIR/" in
  "${HOME%/}"/*) ;;
  *) [ "${VOLE_INSTALL_FORCE:-}" = 1 ] \
       || die "VOLE_INSTALL_LIB is outside \$HOME ($LIB_DIR); set VOLE_INSTALL_FORCE=1 to allow" ;;
esac

command -v curl >/dev/null 2>&1 || die "curl is required"
command -v tar >/dev/null 2>&1 || die "tar is required"
command -v python3 >/dev/null 2>&1 || die "python3 is required (Command Line Tools: xcode-select --install)"

# Python 3.9+
py_ok=$(python3 -c 'import sys; print(1 if sys.version_info >= (3, 9) else 0)' 2>/dev/null || echo 0)
[ "$py_ok" = 1 ] || die "python3 3.9+ required (found: $(python3 --version 2>&1))"

# Local checkout when this script lives next to the vole/ package; otherwise download main.
SCRIPT_PATH=$0
case "$SCRIPT_PATH" in
  /*) ;;
  *) SCRIPT_PATH=$(pwd)/$SCRIPT_PATH ;;
esac
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$SCRIPT_PATH")" 2>/dev/null && pwd) || SCRIPT_DIR=""

SRC=""
if [ -n "${VOLE_REPO:-}" ]; then
  [ -f "$VOLE_REPO/vole/cli.py" ] || die "VOLE_REPO=$VOLE_REPO has no vole/cli.py"
  SRC=$VOLE_REPO
elif [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/vole/cli.py" ]; then
  SRC=$SCRIPT_DIR
fi

TMP=$(mktemp -d "${TMPDIR:-/tmp}/vole-install.XXXXXX")
trap 'rm -rf "$TMP"' EXIT INT HUP TERM

if [ -n "$SRC" ]; then
  echo "installing from local checkout: $SRC"
  mkdir -p "$TMP/src"
  # Copy only what the runtime needs (not .git, tests, personal data).
  cp -R "$SRC/vole" "$TMP/src/vole"
  STAGE=$TMP/src
else
  echo "downloading ${REPO_URL} @ ${BRANCH}…"
  curl -fsSL --connect-timeout 10 --max-time 120 "$TARBALL_URL" -o "$TMP/vole.tar.gz" \
    || die "download failed: $TARBALL_URL"
  mkdir -p "$TMP/extract"
  tar -xzf "$TMP/vole.tar.gz" -C "$TMP/extract"
  # archive root is vole-<branch> (e.g. vole-main)
  STAGE=$(find "$TMP/extract" -maxdepth 1 -type d -name 'vole-*' | head -n 1)
  [ -n "$STAGE" ] && [ -f "$STAGE/vole/cli.py" ] || die "unexpected archive layout"
fi

echo "installing package → $LIB_DIR"
mkdir -p "$LIB_DIR"
# Replace the package tree idempotently; leave anything else in LIB_DIR alone.
rm -rf "$LIB_DIR/vole"
cp -R "$STAGE/vole" "$LIB_DIR/vole"

echo "installing launcher → $BIN_DIR/vole"
mkdir -p "$BIN_DIR"
# Absolute lib path baked in so the launcher works regardless of cwd.
cat > "$BIN_DIR/vole" <<EOF
#!/usr/bin/env python3
"""vole — installed by install.sh"""
import sys
sys.path.insert(0, $(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$LIB_DIR"))
from vole.cli import main
raise SystemExit(main())
EOF
chmod 755 "$BIN_DIR/vole"

# Smoke check
"$BIN_DIR/vole" --help >/dev/null || die "installed vole failed to run"

echo
echo "vole installed."
echo "  package:  $LIB_DIR/vole"
echo "  command:  $BIN_DIR/vole"
echo "  data:     \$HOME/.config/vole/  (created on first scan)"
echo
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    echo "Note: $BIN_DIR is not on your PATH. Add this to your shell config:"
    echo "  export PATH=\"$BIN_DIR:\$PATH\""
    echo
    ;;
esac
echo "Try:"
echo "  vole scan            # scan and create the inventory"
echo "  vole scan --dry-run  # preview without writing"
echo "  vole list"
