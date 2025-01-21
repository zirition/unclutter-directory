[![Tests](https://github.com/zirition/unclutter-directory/workflows/Python%20package/badge.svg)](https://github.com/zirition/unclutter-directory/actions?query=workflow%3APython%20package)

# Unclutter Directory

Unclutter Directory is a Python-based tool for organizing files in a directory according to specified rules. It allows you to move, delete, or compress files based on file conditions such as name patterns, size, and age.

The rules are defined in a YAML file used as a parameter.

## Features
- **Move**: Move files to a specified directory.
- **Delete**: Permanently remove files.
- **Compress**: Compress files into a `.zip` archive.

Using 
- **Customizable Rules**: Define conditions like name patterns, file size, and age for performing actions.
- **Dry Run Mode**: Simulate actions without making actual changes to verify intended effect.
- **Support for Hidden Files**: Option to include hidden files (files starting with a dot).
- **Flexible Deletion Options**: Choose to always delete matched files or never delete them.

## Requirements

- Python 3.13 or higher
- [Click](https://pypi.org/project/click/) 
- [PyYAML](https://pypi.org/project/PyYAML/) 

## Installation

Install using `pip`:
   ```bash
   pip install unclutter-directory
   ```

## Usage

### Command-Line Interface

The project includes a CLI utility powered by Click. You can run the tool using the following commands.

#### Organize

Organize files in a directory based on your rules:

```bash
python -m unclutter-directory organize <target_dir> [<rules_file>] [--dry-run] [--quiet] [--always-delete] [--never-delete] [--include-hidden]
```

- `<target_dir>`: Directory path where the files are to be organized.
- `<rules_file>`: Path to the YAML file containing organization rules. If omitted, it searches for `.unclutter_rules.yaml` in `<target_dir>`.
- `--dry-run`: Optional flag for simulating the actions without making changes.
- `--quiet`: Optional flag to suppress non-error messages.
- `--always-delete`: Optional flag to always delete matched files without confirmation.
- `--never-delete`: Optional flag to never delete matched files.
- `--include-hidden`: Optional flag to include hidden files (files starting with a dot).

### Validate

Validate the structure and attributes of a rules file:

```bash
python -m unclutter-directory validate <rules_file>
```

- `<rules_file>`: Path to the YAML file that contains organization rules.

### Rules File

Define rules in a YAML file. Here is an example:

```yaml
- name: "Process STL Files"
  conditions:
    end: ".stl"
  action:
    type: "move"
    target: "stl_files/"
  check_archive: true

- name: "Process ISO Files"
  conditions:
    end: ".iso"
    older: "2d"
  action:
    type: "move"
    target: "iso_files/"
  check_archive: true
```

The file `example_rules.yaml` contains in the first rule all the options. 

The rules are processed in order, the first rule that is a match is the rule used, so put first the more specific ones.

## Testing

Run the unit tests to verify functionality:

```bash
python -m unittest discover tests
```

## Contributing

Contributions are welcome! 

## License

This project is licensed under the MIT License.

## Contact

You can reach me at `owner of the repo` AT `owner of the repo` DOT `com`