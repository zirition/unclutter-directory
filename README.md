[![PyPI Version](https://img.shields.io/pypi/v/unclutter-directory)](https://pypi.org/project/unclutter-directory/)
[![Python Versions](https://img.shields.io/pypi/pyversions/unclutter-directory)](https://pypi.org/project/unclutter-directory/)
[![Tests](https://github.com/zirition/unclutter-directory/workflows/Python%20package/badge.svg)](https://github.com/zirition/unclutter-directory/actions?query=workflow%3APython%20package)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)


## Table of Contents 📑

- [Features ✨](#features-✨)
- [Installation 📦](#installation-📦)
- [Usage 🚀](#usage-🚀)
- [Rules Format Specification ⚙️](#rules-format-specification-⚙️)
- [Advanced Usage 🔧](#advanced-usage-🔧)
- [Development 👩💻](#development-👩💻)
- [Testing 🧪](#testing-🧪)
- [License 📄](#license-📄)
- [Support 💬](#support-💬)

# Unclutter Directory 🗂️

A powerful and flexible file organization tool that helps you effortlessly declutter your directories by automatically sorting files and folders according to your custom rules. Save time, stay organized, and keep your workspace neat with Unclutter Directory.

A few reasons why Unclutter Directory stands out:

- 🚀 Automate tedious file organization tasks effortlessly
- 🔧 Highly customizable rules to fit any workflow
- 🛡️ Safe operations with dry-run and interactive prompts
- 📦 Supports compression and archive content searching
- 🗑️ Intelligent duplicate detection and cleanup
- 🧪 Actively maintained with comprehensive testing

## Features ✨

- **Multi-Action Support**
  - 🚚 Move files and folders to specific locations with ease
  - 🗑️ Delete obsolete files and folders safely
  - 📦 Compress files and folders into ZIP archives effortlessly
  - 🔍 Search inside ZIP, RAR, and 7Z archives for matching files quickly

- **Unpacked Detection**
  - 🔍 Automatically remove uncompressed directories matching compressed files
  - 🗂️ Compare file structures between archives and directories accurately
  - 🗑️ Interactive prompts for safe removal of uncompressed directories

- **Advanced Matching**
  - Match by name patterns: starts with, ends with, contains, or regex
  - Filter by file size: larger than or smaller than specified thresholds
  - Filter by age: older than or newer than specified durations
  - Apply rules specifically to directories using the `is_directory` flag
  - Support for case-sensitive or insensitive matching

- **Safety & Control**
  - 🧪 Dry-run mode to simulate actions without changes
  - 🔒 Interactive prompts to confirm deletions
  - 📝 Comprehensive and detailed logging for audit trails

## Installation 📦

```bash
pip install unclutter-directory
```

## Usage 🚀

### Basic Command Structure

```bash
unclutter organize [OPTIONS] TARGET_DIR [RULES_FILE]
unclutter validate [OPTIONS] RULES_FILE
unclutter delete-unpacked [OPTIONS] TARGET_DIR
```

### Common Options

| Option           | Description                             |
|------------------|---------------------------------------|
| --dry-run        | Simulate actions without making changes |
| --quiet          | Suppress non-error messages             |
| --include-hidden | Include hidden files and directories    |
| --always-delete  | Skip confirmation prompts for deletions  |
| --never-delete   | Disable all deletion actions             |

**Delete-Unpacked Specific Options:**

| Option           | Description                                   |
|------------------|-----------------------------------------------|
| --dry-run        | Show what would be removed (default behavior) |
| --always-delete  | Remove uncompressed directories without confirmation |
| --never-delete   | Only report matches, don't remove anything    |
| --include-hidden | Include hidden files in structure comparison  |

### Example Workflow

1. Create a rules file (`cleanup_rules.yaml`):
```yaml
- name: "Cleanup Old Downloads"
  conditions:
    older: "30d"
  action:
    type: delete

- name: "Organize Media Files"
  is_directory: false
  conditions:
    regex: "\.(mp4|mov|avi)$"
  action:
    type: move
    target: "media/"

- name: "Archive Projects"
  is_directory: true
  conditions:
    end: "_project"
    newer: "7d"
  action:
    type: compress
    target: "archives/"
```

2. Run organization in dry-run mode to preview changes:
```bash
unclutter organize ~/Downloads cleanup_rules.yaml --dry-run
```

3. Apply changes:
```bash
unclutter organize ~/Downloads cleanup_rules.yaml
```

### Delete Unpacked Command

Remove uncompressed directories that have the same structure as compressed files:

```bash
# Find uncompressed directories in dry-run mode (default)
unclutter delete-unpacked ~/Downloads

# Always remove uncompressed directories without confirmation
unclutter delete-unpacked ~/Downloads --always-delete

# Never delete, only show what would be removed
unclutter delete-unpacked ~/Downloads --never-delete

# Include hidden files in comparison
unclutter delete-unpacked ~/Downloads --include-hidden
```

**How it works:**
- Scans for ZIP/RAR/7Z files in the target directory
- Looks for directories with the same name (without extension)
- Compares file structures between archive and directory
- Prompts for deletion if structures are identical
- Safely handles large directories and archives

## Rules Format Specification ⚙️

The rules file must be a **YAML file** containing a **list of rule dictionaries**. Each rule defines matching criteria and actions to perform on files/directories.

### File Structure

The rules file must be valid YAML in this format:

```yaml
---
# List of rules (at least one rule required)
- name: "Rule Name"        # Optional: Descriptive name (1-200 chars)
  description: "Optional longer description"  # Optional: Description (up to 1000 chars)

  # REQUIRED: Matching conditions (at least one condition required)
  conditions:
    # Pattern matching (strings/regex)
    start: "prefix_"        # Match files starting with pattern
    end: ".ext"             # Match files ending with pattern
    contain: "substring"    # Match files containing pattern
    regex: "^pattern.*$"    # Match files using regex pattern

    # Size conditions (value + unit)
    larger: "100MB"         # Match files larger than size
    smaller: "1GB"          # Match files smaller than size

    # Time conditions (value + unit)
    older: "30d"            # Match files older than time
    newer: "2w"             # Match files newer than time

  # REQUIRED: Action to perform
  action:
    type: "move|delete|compress"  # Action type
    target: "path/"               # Required for move/compress actions

  # OPTIONAL: Behavioral flags (boolean)
  case_sensitive: false     # Case-sensitive pattern matching (default: false)
  check_archive: false      # Search inside ZIP/RAR/7Z archives (default: false)
  is_directory: false       # Apply rule only to directories (default: false)
```

### Rule Fields

#### Required Fields
- **`conditions`**: Dictionary of matching criteria (at least one condition required)
- **`action`**: Dictionary specifying the action to perform

#### Optional Fields
- **`name`**: String (1-200 characters) - Rule identifier/description
- **`description`**: String (up to 1000 characters) - Longer rule description
- **`case_sensitive`**: Boolean - Whether pattern matching is case-sensitive (default: `false`)
- **`check_archive`**: Boolean - Whether to search inside compressed archives (default: `false`)
- **`is_directory`**: Boolean - Whether rule applies only to directories (default: `false`)

### Condition Types

#### Pattern Matching Conditions
These conditions use string matching or regular expressions:

| Condition | Type     | Description | Examples |
|-----------|----------|-------------|----------|
| `start`   | String   | Match files starting with pattern | `"temp_"`, `"report_"` |
| `end`     | String   | Match files ending with pattern | `".pdf"`, `"_backup"` |
| `contain` | String   | Match files containing pattern | `"draft"`, `"2019"` |
| `regex`   | Pattern  | Match files using regex pattern | `"^201\d{2}.*\.pdf$"`, `"\w+\d{3}"` |

#### Size Conditions
Match files based on their size. Format: `<number><unit>` or just `<number>` (defaults to bytes).

| Condition | Description | Unit Examples |
|-----------|-------------|---------------|
| `larger`  | Match files larger than size | `"500MB"`, `"1GB"`, `"1024KB"` |
| `smaller` | Match files smaller than size | `"100MB"`, `"2GB"`, `"512"` (bytes) |

**Supported Size Units:**
- `B` - Bytes (default if no unit specified)
- `KB` - Kilobytes (1024 bytes)
- `MB` - Megabytes (1024² bytes)
- `GB` - Gigabytes (1024³ bytes)

#### Time Conditions
Match files based on modification time. Format: `<number><unit>` or just `<number>` (defaults to seconds).

| Condition | Description | Unit Examples |
|-----------|-------------|---------------|
| `older`   | Match files older than time | `"30d"`, `"2w"`, `"6h"` |
| `newer`   | Match files newer than time | `"1d"`, `"4h"`, `"30m"` |

**Supported Time Units:**
- `s` - Seconds (default if no unit specified)
- `m` - Minutes (60 seconds)
- `h` - Hours (3600 seconds)
- `d` - Days (86400 seconds)
- `w` - Weeks (604800 seconds)

### Action Types

#### Available Actions

| Action Type | Description | Requires `target` | Example |
|------------|-------------|-------------------|---------|
| `move`     | Move files/directories to target path | ✅ Yes | `{"type": "move", "target": "sorted/"}` |
| `delete`   | Delete matching files/directories | ❌ No | `{"type": "delete"}` |
| `compress` | Compress files/directories into ZIP | ✅ Yes | `{"type": "compress", "target": "archives/"}` |

#### Action Field Format

```yaml
action:
  type: "move|delete|compress"        # Required: Action type
  target: "destination/path"          # Required for move/compress
```

**Note:** The `target` parameter:
- Must be a string path
- For `move`: destination directory (relative to working directory)
- For `compress`: directory where compressed file will be created
- Relative paths are supported (e.g., `"subdir/"`, `"../other_dir/"`)
- Directory must exist (will not be auto-created)

### Validation Rules

The rules file is strictly validated. Common validation errors include:

- **File Level:**
  - Must be a YAML list (not a single rule object)
  - Cannot be empty (at least one rule required)
  - File must be readable and ≤10MB

- **Rule Level:**
  - Each rule must be a dictionary object
  - Must contain `conditions` field with at least one valid condition
  - Must contain valid `action` field
  - Optional fields (`name`, `description`) must be strings within length limits
  - Flags (`case_sensitive`, `check_archive`, `is_directory`) must be boolean

- **Condition Level:**
  - Condition keys must be from valid set: `start`, `end`, `contain`, `regex`, `larger`, `smaller`, `older`, `newer`
  - Values cannot be empty/null
  - Size values must follow `<number><unit>` format
  - Time values must follow `<number><unit>` format
  - Regex patterns must be valid regular expressions

- **Action Level:**
  - Must be a dictionary with required `type` field
  - `type` must be one of: `move`, `delete`, `compress`
  - `target` is required for `move` and `compress` actions
  - `target` must be a non-empty string

### Examples

#### Basic File Rule
```yaml
- name: "Organize Office Documents"
  conditions:
    end: ".pdf"
    smaller: "50MB"
  action:
    type: move
    target: "documents/"
```

#### Directory Compression Rule
```yaml
- name: "Compress Old Projects"
  is_directory: true
  conditions:
    older: "6M"
    larger: "100MB"
  action:
    type: compress
    target: "archives/"
```

#### Archive Search Rule
```yaml
- name: "Find Confidential Documents"
  check_archive: true
  case_sensitive: true
  conditions:
    regex: "confidential.*\.docx$"
  action:
    type: move
    target: "classified/"
```

#### Multiple Conditions Rule
```yaml
- name: "Cleanup Old Downloads"
  conditions:
    start: "temp_"
    end: ".tmp"
    older: "7d"
    larger: "10MB"
  action:
    type: delete
```

## Advanced Usage 🔧

### Archive Handling

Search inside compressed files:

```yaml
- name: "Find Secret Documents"
  check_archive: true
  conditions:
    regex: "top_secret.*\.docx$"
  action:
    type: move
    target: "classified/"
```

### Directory Compression

```yaml
- name: "Archive Old Projects"
  is_directory: true
  conditions:
    older: "6M"
  action:
    type: compress
    target: "project_archives/"
```
## Development 👩💻

### Project Setup

```bash
git clone https://github.com/zirition/unclutter-directory
cd unclutter-directory
python -m venv .venv
source .venv/bin/activate  # Linux/MacOS
# .venv\Scripts\activate  # Windows

pip install -e .[dev]  # Install with development dependencies
```


## Testing

```bash
python -m unittest discover tests
```


## License 📄

MIT License

## Contribute 🤝

We welcome contributions! Whether it's bug reports, feature requests, documentation improvements, or code contributions, your help is appreciated.

To contribute:

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Submit a pull request with a clear description of your changes

---

## Support 💬

Have questions, found a bug, or want to request a feature? 

- 🐞 Open an issue on GitHub: [https://github.com/zirition/unclutter-directory/issues](https://github.com/zirition/unclutter-directory/issues)

