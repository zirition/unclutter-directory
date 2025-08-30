from pathlib import Path
from typing import List, Optional

import yaml

from ..commons import validations
from ..commons.validations import Rules, validate_rules_file
from ..config.organize_config import OrganizeConfig
from .base import Validator

# Usar el logger de commons
logger = validations.get_logger()


class RulesFileValidator(Validator):
    """
    Validates rules file existence, format, and content.

    This validator performs comprehensive validation of:
    1. Rules file existence and accessibility
    2. File format (YAML structure)
    3. Rule structure compliance
    4. Condition and action validity

    Uses safe YAML loading to prevent code injection attacks.
    """

    def validate(self, config: OrganizeConfig) -> List[str]:
        """
        Validate rules file and its content.

        Performs multi-step validation:
        1. Resolves rules file path (auto-detects if not specified)
        2. Checks file existence and permissions
        3. Validates YAML parsing and structure
        4. Validates individual rule content

        Args:
            config: Configuration to validate (rules_file path may be auto-detected/updated)

        Returns:
            List[str]: List of validation errors (empty if validation passes)
        """
        errors = []

        # Step 1: Resolve rules file path
        if not config.rules_file:
            default_rules = config.target_dir / ".unclutter_rules.yaml"
            if default_rules.exists():
                config.rules_file = str(default_rules)
            else:
                errors.append(
                    "No rules file specified and no default .unclutter_rules.yaml found in target directory"
                )
                return errors

        # Step 2: Validate file path and accessibility
        rules_path = Path(config.rules_file)

        if not rules_path.exists():
            errors.append(f"Rules file does not exist: {config.rules_file}")
            return errors

        if not rules_path.is_file():
            errors.append(f"Rules path is not a regular file: {config.rules_file}")
            return errors

        # Check file size (prevent extremely large files causing memory issues)
        file_size = rules_path.stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            errors.append(
                f"Rules file too large ({file_size / (1024 * 1024):.1f}MB, max 10MB)"
            )
            return errors

        if file_size == 0:
            errors.append("Rules file is empty")
            return errors

        # Check file permissions (readable)
        if not rules_path.stat().st_mode & 0o400:  # Check read permission
            errors.append(f"Rules file is not readable: {config.rules_file}")
            return errors

        # Step 3: Load and validate content
        try:
            rules = self._load_rules(config.rules_file)
            if rules is None:
                errors.append("Failed to load rules from file")
                return errors

            # Step 4: Validate rule structure and content
            validation_errors = validate_rules_file(rules)
            if validation_errors:
                errors.extend(validation_errors)

        except MemoryError:
            errors.append("Rules file too large to load into memory")
        except PermissionError:
            errors.append(f"Permission denied reading rules file: {config.rules_file}")
        except OSError as e:
            errors.append(f"OS error reading rules file: {e}")
        except Exception as e:
            errors.append(f"Unexpected error validating rules file: {e}")

        return errors

    def _load_rules(self, rules_file: str) -> Optional[Rules]:
        """
        Load rules from YAML file with comprehensive error handling.

        Uses safe_load to prevent code injection attacks.
        Validates basic structure after loading.

        Args:
            rules_file: Path to rules file

        Returns:
            Loaded rules as Rules type or None if loading failed
        """
        try:
            with open(rules_file, encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    logger.error("Rules file is empty or contains only whitespace")
                    return None

                rules = yaml.safe_load(content)

            if rules is None:
                logger.error("Rules file is empty (None content)")
                return None

            if not isinstance(rules, list):
                logger.error(
                    f"Rules file must contain a list of rules, got {type(rules).__name__}: {rules}"
                )
                return None

            if not rules:  # Empty list
                logger.error("Rules file contains empty list")
                return None

            return rules

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in rules file '{rules_file}': {e}")
            return None
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading rules file '{rules_file}': {e}")
            return None
        except FileNotFoundError:
            logger.error(f"Rules file not found: {rules_file}")
            return None
        except IsADirectoryError:
            logger.error(f"Path is a directory, not a file: {rules_file}")
            return None
        except PermissionError:
            logger.error(f"Permission denied reading rules file: {rules_file}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading rules file '{rules_file}': {e}")
            return None
