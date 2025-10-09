#!/bin/bash
#
# Installation script for gh-milestone shell completion
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASH_COMPLETION_DIR="$SCRIPT_DIR/bash"
ZSH_COMPLETION_DIR="$SCRIPT_DIR/zsh"

echo "Installing gh-milestone shell completion..."

# Detect shell
SHELL_NAME="$(basename "$SHELL")"
echo "Detected shell: $SHELL_NAME"

case "$SHELL_NAME" in
    bash)
        echo "Installing bash completion..."
        
        # Common bash completion directories
        BASH_COMPLETION_DIRS=(
            "/etc/bash_completion.d"
            "/usr/local/etc/bash_completion.d"
            "$HOME/.bash_completion.d"
            "$HOME/.local/share/bash-completion/completions"
        )
        
        COMPLETION_INSTALLED=false
        
        for dir in "${BASH_COMPLETION_DIRS[@]}"; do
            if [[ -d "$dir" && -w "$dir" ]]; then
                echo "Installing to $dir"
                cp "$BASH_COMPLETION_DIR/gh-milestone" "$dir/"
                COMPLETION_INSTALLED=true
                break
            fi
        done
        
        if [[ "$COMPLETION_INSTALLED" == false ]]; then
            echo "Could not find writable bash completion directory."
            echo "You can manually install by adding the following to your ~/.bashrc:"
            echo "  source $BASH_COMPLETION_DIR/gh-milestone"
        else
            echo "Bash completion installed successfully!"
            echo "Please restart your shell or run: source ~/.bashrc"
        fi
        ;;
        
    zsh)
        echo "Installing zsh completion..."
        
        # Common zsh completion directories
        ZSH_COMPLETION_DIRS=(
            "/usr/local/share/zsh/site-functions"
            "/usr/share/zsh/site-functions"
            "$HOME/.zsh/completions"
            "$HOME/.zsh/functions"
        )
        
        # Check if oh-my-zsh is installed
        if [[ -d "$HOME/.oh-my-zsh" ]]; then
            ZSH_COMPLETION_DIRS=("$HOME/.oh-my-zsh/completions" "${ZSH_COMPLETION_DIRS[@]}")
        fi
        
        COMPLETION_INSTALLED=false
        
        for dir in "${ZSH_COMPLETION_DIRS[@]}"; do
            if [[ -d "$dir" && -w "$dir" ]]; then
                echo "Installing to $dir"
                cp "$ZSH_COMPLETION_DIR/_gh-milestone" "$dir/"
                COMPLETION_INSTALLED=true
                break
            elif [[ ! -d "$dir" ]]; then
                echo "Creating directory $dir"
                mkdir -p "$dir"
                cp "$ZSH_COMPLETION_DIR/_gh-milestone" "$dir/"
                COMPLETION_INSTALLED=true
                break
            fi
        done
        
        if [[ "$COMPLETION_INSTALLED" == false ]]; then
            echo "Could not find writable zsh completion directory."
            echo "You can manually install by adding the following to your ~/.zshrc:"
            echo "  fpath=($ZSH_COMPLETION_DIR \$fpath)"
            echo "  autoload -U compinit && compinit"
        else
            echo "Zsh completion installed successfully!"
            echo "Please restart your shell or run: source ~/.zshrc"
        fi
        ;;
        
    *)
        echo "Unsupported shell: $SHELL_NAME"
        echo "Manual installation:"
        echo "  For bash: cp $BASH_COMPLETION_DIR/gh-milestone /etc/bash_completion.d/"
        echo "  For zsh: cp $ZSH_COMPLETION_DIR/_gh-milestone /usr/local/share/zsh/site-functions/"
        ;;
esac

echo ""
echo "To test completion, try typing:"
echo "  gh-milestone <TAB>"
echo "  milestone <TAB>"
echo ""
echo "Note: Make sure jq is installed for roadmap file completion:"
echo "  Ubuntu/Debian: sudo apt-get install jq"
echo "  macOS: brew install jq"
echo "  Other systems: Check your package manager"