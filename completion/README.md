# Shell Completion and Aliases for gh-milestone

This directory contains shell completion scripts and command aliases to enhance your productivity when using the gh-milestone CLI tool.

## Installation

### Automatic Installation

Run the installation script:

```bash
./completion/install-completion.sh
```

This script will:
1. Detect your shell type (bash/zsh)
2. Install completion scripts to the appropriate directory
3. Provide instructions for manual installation if needed

### Manual Installation

#### Bash Completion

1. Copy the completion script:
   ```bash
   sudo cp completion/bash/gh-milestone /etc/bash_completion.d/
   # OR for user-specific installation:
   mkdir -p ~/.bash_completion.d
   cp completion/bash/gh-milestone ~/.bash_completion.d/
   ```

2. Add to your `~/.bashrc`:
   ```bash
   # Load bash completion
   [ -f ~/.bash_completion.d/gh-milestone ] && . ~/.bash_completion.d/gh-milestone
   ```

3. Restart your shell or run:
   ```bash
   source ~/.bashrc
   ```

#### Zsh Completion

1. Copy the completion script:
   ```bash
   sudo cp completion/zsh/_gh-milestone /usr/local/share/zsh/site-functions/
   # OR for user-specific installation:
   mkdir -p ~/.zsh/completions
   cp completion/zsh/_gh-milestone ~/.zsh/completions/
   ```

2. Add to your `~/.zshrc`:
   ```bash
   # Add completion directory to fpath
   fpath=($HOME/.zsh/completions $fpath)
   autoload -U compinit && compinit
   ```

3. Restart your shell or run:
   ```bash
   source ~/.zshrc
   ```

## Command Aliases

### Loading Aliases

Source the aliases file in your shell configuration:

```bash
# Add to ~/.bashrc or ~/.zshrc
source /path/to/gh-milestone-cli/completion/aliases.sh
```

### Available Aliases

#### Basic Command Aliases

| Alias | Full Command | Description |
|-------|-------------|-------------|
| `ghmc` | `gh milestone create` | Create GitHub issues from roadmap |
| `ghmv` | `gh milestone validate` | Validate roadmap file against schema |
| `ghmd` | `gh milestone delete` | Delete GitHub issues from roadmap |
| `ghmu` | `gh milestone update` | Update existing GitHub issues from roadmap |
| `ghml` | `gh milestone list` | List current hierarchy and state |
| `ghms` | `gh milestone status` | Show progress and completion status |
| `ghmvc` | `gh milestone validate-state` | Validate state file entries |
| `ghmm` | `gh milestone migrate-state` | Migrate state file to current format |
| `ghmsync` | `gh milestone sync` | Synchronize state with GitHub and roadmap |

#### Verbose Aliases

| Alias | Full Command | Description |
|-------|-------------|-------------|
| `ghmcv` | `gh milestone create --verbose` | Create issues with verbose output |
| `ghmvv` | `gh milestone validate --verbose` | Validate with verbose output |
| `ghmdv` | `gh milestone delete --verbose` | Delete with verbose output |
| `ghmuv` | `gh milestone update --verbose` | Update with verbose output |
| `ghmlv` | `gh milestone list --verbose` | List with verbose output |
| `ghmsv` | `gh milestone status --verbose` | Show status with verbose output |

#### Format-Specific Aliases

| Alias | Full Command | Description |
|-------|-------------|-------------|
| `ghmlt` | `gh milestone list --format tree` | List in tree format |
| `ghmlb` | `gh milestone list --format table` | List in table format |
| `ghmlj` | `gh milestone list --format json` | List in JSON format |
| `ghmlm` | `gh milestone list --show-missing` | List including missing issues |
| `ghmss` | `gh milestone status --format summary` | Show summary status |
| `ghmsd` | `gh milestone status --format detailed` | Show detailed status |
| `ghmsj` | `gh milestone status --format json` | Show status in JSON format |

#### Dry-Run Aliases

| Alias | Full Command | Description |
|-------|-------------|-------------|
| `ghmdry` | `gh milestone create --dry-run` | Show what would be created |
| `ghmdryv` | `gh milestone create --dry-run --verbose` | Show what would be created (verbose) |
| `ghmvc-dry` | `gh milestone validate-state --cleanup --dry-run` | Show what would be cleaned up |
| `ghmm-dry` | `gh milestone migrate-state --dry-run` | Show what would be migrated |
| `ghmsync-dry` | `gh milestone sync --dry-run` | Show what would be synced |

#### Quick Aliases

| Alias | Full Command | Description |
|-------|-------------|-------------|
| `ghmq` | `gh milestone validate` | Quick validation |
| `ghmqv` | `gh milestone validate --verbose` | Quick validation (verbose) |
| `ghmsq` | `gh milestone status` | Quick status check |
| `ghmsqv` | `gh milestone status --verbose` | Quick status check (verbose) |

#### Schema-Related Aliases

| Alias | Full Command | Description |
|-------|-------------|-------------|
| `ghmc-custom` | `gh milestone create --schema` | Create with custom schema |
| `ghmv-custom` | `gh milestone validate --schema` | Validate with custom schema |
| `ghmu-custom` | `gh milestone update --schema` | Update with custom schema |
| `ghml-custom` | `gh milestone list --schema` | List with custom schema |
| `ghms-custom` | `gh milestone status --schema` | Show status with custom schema |

#### Help Aliases

| Alias | Full Command | Description |
|-------|-------------|-------------|
| `ghmhelp` | `gh milestone --help` | Show main help |
| `ghmchelp` | `gh milestone create --help` | Show create command help |
| `ghmvhelp` | `gh milestone validate --help` | Show validate command help |
| `ghmdhelp` | `gh milestone delete --help` | Show delete command help |
| `ghmuhelp` | `gh milestone update --help` | Show update command help |
| `ghmlhelp` | `gh milestone list --help` | Show list command help |
| `ghmshelp` | `gh milestone status --help` | Show status command help |
| `ghmvchelp` | `gh milestone validate-state --help` | Show validate-state help |
| `ghmmhelp` | `gh milestone migrate-state --help` | Show migrate-state help |
| `ghmsynchelp` | `gh milestone sync --help` | Show sync help |

### Function Aliases

#### `ghm-create-validate <file>`
Create issues from roadmap, then validate the result:
```bash
ghm-create-validate roadmap.json
```

#### `ghm-status-detailed <file>`
Show both summary and detailed status:
```bash
ghm-status-detailed roadmap.json
```

#### `ghm-list-all <file>`
Show tree view, table view, and missing issues:
```bash
ghm-list-all roadmap.json
```

#### `ghm-sync-validate <file>`
Sync state with GitHub and roadmap, then validate:
```bash
ghm-sync-validate roadmap.json
```

#### `ghm-workflow <file>`
Complete workflow: validate, create, check status, and list issues:
```bash
ghm-workflow roadmap.json
```

## Usage Examples

### With Completion

After installing completion, you can:

```bash
# Complete commands
gh milestone <TAB>
# Shows: create validate delete update list status validate-state migrate-state sync

# Complete files
gh milestone create <TAB>
# Shows: *.json files in current directory

# Complete options
gh milestone create --<TAB>
# Shows: --schema --verbose --help

# Complete milestone names (if jq is installed)
gh milestone delete --milestone <TAB>
# Shows: milestone names from roadmap file

# Complete task names (if jq is installed)
gh milestone delete --task <TAB>
# Shows: task names from roadmap file
```

### With Aliases

```bash
# Quick workflow
ghmq roadmap.json                    # Quick validation
ghmc roadmap.json                    # Create issues
ghms roadmap.json                    # Check status
ghml roadmap.json                    # List issues

# Complete workflow with function
ghm-workflow roadmap.json            # Full workflow in one command

# Dry-run before actual operations
ghmdry roadmap.json                  # See what would be created
ghmsync-dry roadmap.json            # See what would be synced

# Different output formats
ghmlt roadmap.json                   # Tree format
ghmlb roadmap.json                   # Table format
ghmlj roadmap.json                   # JSON format
ghmlm roadmap.json                   # Include missing issues
```

## Requirements

### For Completion

- **bash**: Standard bash completion (usually included with bash)
- **zsh**: Standard zsh completion (usually included with zsh)
- **jq**: Required for roadmap file completion (milestone/task names)
  - Ubuntu/Debian: `sudo apt-get install jq`
  - macOS: `brew install jq`
  - Other systems: Check your package manager

### For Aliases

- No additional requirements beyond the gh-milestone CLI tool

## Troubleshooting

### Completion Not Working

1. **Bash**:
   - Ensure completion script is in `/etc/bash_completion.d/` or `~/.bash_completion.d/`
   - Check that `~/.bashrc` sources the completion file
   - Restart your shell or run `source ~/.bashrc`

2. **Zsh**:
   - Ensure completion script is in site-functions directory
   - Check that `fpath` includes the completion directory in `~/.zshrc`
   - Run `compinit` manually: `autoload -U compinit && compinit`
   - Restart your shell or run `source ~/.zshrc`

3. **File Completion Not Working**:
   - Install `jq` for roadmap file completion
   - Ensure roadmap files are valid JSON
   - Check file permissions

### Aliases Not Working

1. **Aliases Not Recognized**:
   - Ensure you've sourced the aliases file: `source completion/aliases.sh`
   - Check that the source command is in your shell rc file
   - Restart your shell or re-source your rc file

2. **Function Aliases Not Working**:
   - Ensure functions are exported: `export -f function-name`
   - Check that the aliases file is sourced after function definitions

### Common Issues

- **Permission Denied**: Use user-specific directories instead of system directories
- **Directory Not Found**: Create the directory first with `mkdir -p`
- **Completion Not Loading**: Check shell configuration and restart shell
- **jq Not Found**: Install jq for enhanced completion features

## Contributing

To add new aliases or improve completion:

1. **Aliases**: Edit `completion/aliases.sh`
2. **Bash Completion**: Edit `completion/bash/gh-milestone`
3. **Zsh Completion**: Edit `completion/zsh/_gh-milestone`
4. **Installation**: Update `completion/install-completion.sh`

Test your changes by sourcing the modified files and verifying functionality.