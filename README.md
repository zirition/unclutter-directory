[![PyPI Version](https://img.shields.io/pypi/v/unclutter-directory)](https://pypi.org/project/unclutter-directory/)
[![Python Versions](https://img.shields.io/pypi/pyversions/unclutter-directory)](https://pypi.org/project/unclutter-directory/)
[![Tests](https://github.com/zirition/unclutter-directory/workflows/Python%20package/badge.svg)](https://github.com/zirition/unclutter-directory/actions?query=workflow%3APython%20package)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)


# Unclutter Directory 🗂️

A smart file organization tool that automatically sorts your files and directories based on customizable rules.

## Features ✨

- **Multi-Action Support**
  - 🚚 Move files/directories to specific locations
  - 🗑️ Delete obsolete items
  - 📦 Compress files/directories to ZIP archives
  - 🔍 Search inside ZIP/RAR archives for matching files

- **Advanced Matching**
  - Name patterns (starts/ends with, contains, regex)
  - File size thresholds (larger/smaller than)
  - Age conditions (older/newer than)
  - Directory-specific rules (`is_directory` flag)
  - Case-sensitive/insensitive matching

- **Safety & Control**
  - 🧪 Dry-run simulation mode
  - 🔒 Interactive deletion prompts
  - 📝 Comprehensive logging

## Installation 📦

  ```bash
  pip install unclutter-directory
   ```

## Usage 🚀

### Basic Command Structure

```bash
unclutter organize [OPTIONS] TARGET_DIR [RULES_FILE]
unclutter validate [OPTIONS] RULES_FILE
```

### Common Options

| Option           | Description                             |
|------------------|-----------------------------------------|
| --dry-run        | Simulate actions without making changes |
| --quiet	         | Suppress non-error messages             |
| --include-hidden | Process hidden files/directories        |
| --always-delete  | Skip confirmation for deletions         |
| --never-delete   | Prevent all deletion actions            |

### Example Workflow

1. Create rules file (`cleanup_rules.yaml`):
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

2. Run organization:
```bash
unclutter organize ~/Downloads cleanup_rules.yaml --dry-run
```
Apply changes:
```bash
unclutter organize ~/Downloads cleanup_rules.yaml
```
## Rules Configuration ⚙️

### Rule Structure

```yaml
- name: "Rule Name"
  is_directory: false  # Optional (default: false)
  case_sensitive: false  # Optional (default: false)
  check_archive: true  # Optional (default: false)
  conditions:
    start: "report_"
    end: ".pdf"
    larger: "10MB"
    older: "2w"
  action:
    type: move
    target: "documents/"
```

### Condition Types

| Condition | Format           | Examples                |
|-----------|------------------|-------------------------|
| Time      | `<number><unit>` | `30d`, `2h`, `15m`      |
| Size      | `<number><unit>` | `500MB`, `1GB`, `100KB` |
| Name      | String/Regex     | `start: "temp_"`        |

Time Units: `s` (seconds), `m` (minutes), `h` (hours), `d` (days), `w` (weeks)

Size Units: `B`, `KB`, `MB`, `GB`

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

## Support 💬

For issues and feature requests, please [open an issue](https://github.com/zirition/unclutter-directory/issues).
