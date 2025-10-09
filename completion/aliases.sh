#!/bin/bash
#
# Command aliases for gh-milestone CLI
#

# Source this file in your shell rc file (~/.bashrc, ~/.zshrc, etc.)
# or copy the aliases directly to your rc file.

echo "Loading gh-milestone aliases..."

# Basic command aliases
alias ghmc='gh milestone create'
alias ghmv='gh milestone validate'
alias ghmd='gh milestone delete'
alias ghmu='gh milestone update'
alias ghml='gh milestone list'
alias ghms='gh milestone status'
alias ghmvc='gh milestone validate-state'
alias ghmm='gh milestone migrate-state'
alias ghmsync='gh milestone sync'

# Common operation aliases
alias ghmcv='gh milestone create --verbose'
alias ghmvv='gh milestone validate --verbose'
alias ghmdv='gh milestone delete --verbose'
alias ghmuv='gh milestone update --verbose'
alias ghmlv='gh milestone list --verbose'
alias ghmsv='gh milestone status --verbose'

# Format-specific aliases
alias ghmlt='gh milestone list --format tree'
alias ghmlb='gh milestone list --format table'
alias ghmlj='gh milestone list --format json'
alias ghmlm='gh milestone list --show-missing'

alias ghmss='gh milestone status --format summary'
alias ghmsd='gh milestone status --format detailed'
alias ghmsj='gh milestone status --format json'

# Dry-run aliases for safe operations
alias ghmdry='gh milestone create --dry-run'
alias ghmdryv='gh milestone create --dry-run --verbose'
alias ghmvc-dry='gh milestone validate-state --cleanup --dry-run'
alias ghmm-dry='gh milestone migrate-state --dry-run'
alias ghmsync-dry='gh milestone sync --dry-run'

# Quick validation and status aliases
alias ghmq='gh milestone validate'  # Quick validation
alias ghmqv='gh milestone validate --verbose'
alias ghmsq='gh milestone status'   # Quick status
alias ghmsqv='gh milestone status --verbose'

# Schema-related aliases
alias ghmc-custom='gh milestone create --schema'
alias ghmv-custom='gh milestone validate --schema'
alias ghmu-custom='gh milestone update --schema'
alias ghml-custom='gh milestone list --schema'
alias ghms-custom='gh milestone status --schema'

# Help aliases
alias ghmhelp='gh milestone --help'
alias ghmchelp='gh milestone create --help'
alias ghmvhelp='gh milestone validate --help'
alias ghmdhelp='gh milestone delete --help'
alias ghmuhelp='gh milestone update --help'
alias ghmlhelp='gh milestone list --help'
alias ghmshelp='gh milestone status --help'
alias ghmvchelp='gh milestone validate-state --help'
alias ghmhelp='gh milestone migrate-state --help'
alias ghmsynchelp='gh milestone sync --help'

# Function-based aliases for more complex operations
ghm-create-validate() {
    echo "Creating issues from roadmap: $1"
    gh milestone create "$1"
    echo "Validating created issues..."
    gh milestone validate "$1"
}

ghm-status-detailed() {
    echo "=== Status Summary ==="
    gh milestone status "$1"
    echo ""
    echo "=== Detailed Status ==="
    gh milestone status "$1" --detailed
}

ghm-list-all() {
    echo "=== Tree View ==="
    gh milestone list "$1" --format tree
    echo ""
    echo "=== Table View ==="
    gh milestone list "$1" --format table
    echo ""
    echo "=== Missing Issues ==="
    gh milestone list "$1" --show-missing
}

ghm-sync-validate() {
    echo "=== Syncing State ==="
    gh milestone sync "$1"
    echo ""
    echo "=== Validating State ==="
    gh milestone validate-state "$1" --cleanup
}

ghm-workflow() {
    local roadmap_file="$1"
    if [[ -z "$roadmap_file" ]]; then
        echo "Usage: ghm-workflow <roadmap-file>"
        return 1
    fi
    
    echo "=== gh-milestone Workflow ==="
    echo "Roadmap file: $roadmap_file"
    echo ""
    
    echo "1. Validating roadmap..."
    gh milestone validate "$roadmap_file"
    echo ""
    
    echo "2. Creating issues..."
    gh milestone create "$roadmap_file"
    echo ""
    
    echo "3. Checking status..."
    gh milestone status "$roadmap_file"
    echo ""
    
    echo "4. Listing created issues..."
    gh milestone list "$roadmap_file"
    echo ""
    
    echo "Workflow completed!"
}

# Export functions
export -f ghm-create-validate
export -f ghm-status-detailed
export -f ghm-list-all
export -f ghm-sync-validate
export -f ghm-workflow

echo "gh-milestone aliases loaded successfully!"
echo ""
echo "Common aliases:"
echo "  ghmc     - gh milestone create"
echo "  ghmv     - gh milestone validate"
echo "  ghml     - gh milestone list"
echo "  ghms     - gh milestone status"
echo "  ghmdry   - gh milestone create --dry-run"
echo ""
echo "Function aliases:"
echo "  ghm-workflow <file>     - Complete workflow: validate, create, status, list"
echo "  ghm-create-validate <file> - Create issues then validate"
echo "  ghm-status-detailed <file> - Show both summary and detailed status"
echo "  ghm-list-all <file>     - Show tree, table, and missing issues"
echo "  ghm-sync-validate <file> - Sync state then validate"
echo ""
echo "Use 'ghmhelp' for main help or 'ghm<command>help' for command-specific help."