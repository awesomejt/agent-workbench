#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
BIN_SRC="$REPO_ROOT/cli/builds/awb"

# Build if binary is missing
if [ ! -f "$BIN_SRC" ]; then
    echo "awb binary not found — building..."
    make -C "$REPO_ROOT" build-cli
fi

# Choose install directory: prefer ~/.local/bin, fall back to ~/bin (create if absent)
if [ -d "$HOME/.local/bin" ]; then
    INSTALL_DIR="$HOME/.local/bin"
elif [ -d "$HOME/bin" ]; then
    INSTALL_DIR="$HOME/bin"
else
    INSTALL_DIR="$HOME/bin"
    mkdir -p "$INSTALL_DIR"
    echo "Created $INSTALL_DIR"
fi

cp "$BIN_SRC" "$INSTALL_DIR/awb"
chmod +x "$INSTALL_DIR/awb"
echo "Installed: $INSTALL_DIR/awb"

# Warn if the install dir is not on PATH
case ":$PATH:" in
    *":$INSTALL_DIR:"*) ;;
    *)
        echo ""
        echo "Note: $INSTALL_DIR is not in your PATH. Add to your shell profile:"
        echo "  export PATH=\"\$HOME/${INSTALL_DIR#"$HOME"/}:\$PATH\""
        ;;
esac
