# Unclutter Directory

Unclutter Directory is a Python-based tool for organizing files in a directory according to specified rules. It allows you to move, delete, or compress files based on file conditions such as name patterns, size, and age. The project utilizes a rules file that defines the conditions and actions for file management.

## Features
- **Move**: Move files to a specified directory.
- **Delete**: Permanently remove files.
- **Compress**: Compress files into a `.zip` archive.

Using 
- **Customizable Rules**: Define conditions like name patterns, file size, and age for performing actions.
- **Dry Run Mode**: Simulate actions without making actual changes to verify intended effect.

## Requirements

- Python 3.13 or higher
- [Click](https://pypi.org/project/click/) 
- [PyYAML](https://pypi.org/project/PyYAML/) 

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/zirition/unclutter_directory.git
   ```

2. Change into the project directory:
   ```bash
   cd unclutter_directory
   ```

3. Install dependencies:
   ```bash
   uv sync
   ```

## Usage

### Command-Line Interface

The project includes a CLI utility powered by Click. You can run the tool using the following commands.

#### Organize

Organize files in a directory based on your rules:

```bash
python -m unclutter_directory organize <rules_file> <target_dir> [--dry-run]
```

- `<rules_file>`: Path to the YAML file that contains organization rules.
- `<target_dir>`: Directory path where the files are to be organized.
- `--dry-run`: Optional flag for simulating the actions without making changes.

#### Validate

Validate the structure and attributes of a rules file:

```bash
python -m unclutter_directory validate <rules_file>
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

For more information, contact [zirition@zirition.com].
