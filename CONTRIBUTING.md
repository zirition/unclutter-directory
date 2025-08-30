# Contributing to Unclutter Directory 🤝

Thank you for your interest in contributing to Unclutter Directory! We welcome contributions of all kinds.

## Ways to Contribute

- 🐛 **Bug reports** via GitHub issues
- 📝 **Documentation improvements**
- 💡 **Feature requests**
- 🛠️ **Code contributions** via pull requests
- 🧪 **Tests and tooling improvements**

## Development Setup

### Prerequisites

- Python 3.8 or higher
- git

### Installation

```bash
git clone https://github.com/zirition/unclutter-directory
cd unclutter-directory
uv sync --dev  # Install with development dependencies
```

### Basic Commands

```bash
# Run tests
uv run -m unittest discover tests

# Code formatting and linting
uv run ruff check .
uv run ruff format .

# Building
uv build
```

## Versioning and Releases 📋

This project uses **setuptools-scm** for automatic versioning based on Git tags.

### Current Version Format
- Version is dynamically generated from the last git tag
- Format: `{tag}.{dev}{commits}+{hash}` (e.g., `1.0.1.dev3+g1234567`)
- When repo has no commits since tag: just the tag (e.g., `1.0.1`)

### Git Tags
- Tags should follow semantic versioning: `x.y.z` (e.g., `1.0.0`, `1.1.2`)
- Tags without 'v' prefix (aligns with current tags: `0.9.0`, `0.9.1`, etc.)

### Release Process

#### For Maintainers:
To create a new release:

1. **Manual Release**:
   - Go to GitHub Actions → "Create Release" workflow
   - Click "Run workflow"
   - Fill in the tag name (e.g., `1.0.0`), title, and description
   - Optionally mark as pre-release

2. **Automated Publishing**:
   - After tag is created, `python-publish.yml` workflow automatically:
     - Runs tests
     - Builds package
     - Uploads to PyPI

#### For Contributors:
- Normal development: version will be `{last_tag}.dev{commits}+dirty` during development
- After tag: version matches the tag exactly

### CI/CD Pipeline

- **Quality Checks** (on push/PR to main):
  - Lint: ruff (code quality)
  - Format: ruff format check
  - Tests: unittest across Python 3.9-3.12

- **Release on Tag**:
  - Tests are run before building
  - Package is built with `uv build`
  - Published to PyPI automatically

## Development Guidelines

### Code Style
- We use Python 3.8+ with type hints
- Code is formatted with ruff's black-compatible formatter
- Line length: 88 characters (black default)
- Follow PEP 8 conventions

### Commit Messages
Please use clear, descriptive commit messages:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test-related changes
- `refactor:` for code refactoring

### Pull Request Process

1. **Fork the repository** and create your branch from `main`
2. **Make your changes**, ensuring tests pass locally
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description

### Testing
- All tests must pass before merging
- Aim for good test coverage
- Use descriptive test names
- Test edge cases and error conditions

## Project Structure

```
├── unclutter_directory/        # Main package
│   ├── __init__.py           # Package initialization
│   ├── cli.py               # Command line interface
│   ├── commands/           # CLI commands
│   ├── config/            # Configuration handling
│   ├── entities/          # Core data models
│   ├── validation/        # Input validation
│   └── ...
├── tests/                  # Test suite
├── .github/                # GitHub Actions workflows
├── pyproject.toml         # Project configuration
└── README.md             # Main documentation
```

## Getting Help

- 📖 Read the [main README](README.md) for usage instructions
- 🐞 [Open an issue](https://github.com/zirition/unclutter-directory/issues) for bugs or feature requests
- 💬 Start a discussion for general questions

Thank you for contributing to Unclutter Directory! 🎉