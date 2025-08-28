import sys
import logging
import re
from typing import List, Dict, Any

from unclutter_directory.commons.parsers import parse_size, parse_time

# Type aliases
Rules = List[dict]

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("unclutter_directory")

def get_logger():
    return logger

# Constantes para validación
VALID_CONDITIONS = {
    "start", "end", "contain", "regex",
    "larger", "smaller", "older", "newer"
}
VALID_ACTIONS = {"move", "delete", "compress"}

def _validate_condition(rule_num: int, key: str, value: str) -> List[str]:
    """
    Validate individual condition key-value pair.

    Args:
        rule_num: Rule number for error reporting
        key: Condition name (start, end, contain, regex, larger, smaller, older, newer)
        value: Condition value as string

    Returns:
        List[str]: List of validation errors (empty if valid)

    Note:
        This function validates individual condition values without checking
        if the condition key itself is valid (that's handled elsewhere).
    """
    errors = []

    if key in {"larger", "smaller"}:
        try:
            parse_size(value)
        except ValueError as e:
            errors.append(f"Rule #{rule_num}: Invalid size value '{value}' for '{key}' - {e}")

    elif key in {"older", "newer"}:
        try:
            parse_time(value)
        except ValueError as e:
            errors.append(f"Rule #{rule_num}: Invalid time value '{value}' for '{key}' - {e}")

    elif key == "regex":
        try:
            re.compile(value)
        except re.error as e:
            errors.append(f"Rule #{rule_num}: Invalid regex pattern '{value}' - {e}")

    return errors

def _validate_action(rule_num: int, action: Dict[str, Any]) -> List[str]:
    """
    Validate action dictionary from a rule.

    Args:
        rule_num: Rule number for error reporting
        action: Action dictionary with 'type' and optional 'target'

    Returns:
        List[str]: List of validation errors (empty if valid)

    Examples:
        Valid actions:
        - {"type": "move", "target": "/path/to/dest"}
        - {"type": "delete"}
        - {"type": "compress", "target": "."}
    """
    errors = []
    action_type = action.get("type")

    if not action_type:
        errors.append(f"Rule #{rule_num}: Action missing required 'type' field")
    elif action_type not in VALID_ACTIONS:
        errors.append(f"Rule #{rule_num}: Invalid action type '{action_type}' - valid options: {', '.join(VALID_ACTIONS)}")
    elif action_type in ["move", "compress"] and not action.get("target"):
        errors.append(f"Rule #{rule_num}: '{action_type}' action requires 'target' parameter")

    target = action.get("target")
    if target and not isinstance(target, str):
        errors.append(f"Rule #{rule_num}: Target must be a string, got {type(target).__name__}")

    # Validate target path safety (basic check)
    if target and isinstance(target, str):
        if target.startswith("..") or any(part in target.split("/") for part in ["../../../..", "...."]):
            errors.append(f"Rule #{rule_num}: Target path contains suspicious patterns")

    return errors

def validate_rules_file(rules: List) -> List[str]:
    """
    Validate complete rules file structure and content.

    Performs comprehensive validation of:
    - File format (must be list)
    - Rule structure (must be dictionaries)
    - Condition keys (must be valid)
    - Condition values (must be valid per type)
    - Action structure (must be dictionaries)
    - Action types (must be valid)
    - Optional fields (name, description, case_sensitive, check_archive, is_directory)

    Args:
        rules: List of rule dictionaries to validate

    Returns:
        List[str]: List of validation errors (empty if all rules are valid)

    Example of a valid rule:
        {
            "name": "Optional description",
            "conditions": {
                "larger": "100MB",
                "older": "30d"
            },
            "action": {
                "type": "move",
                "target": "old_files/"
            },
            "case_sensitive": False,
            "check_archive": True,
            "is_directory": False
        }
    """
    errors = []
    
    if not isinstance(rules, list):
        return ["Rules file must be a list of rule dictionaries"]

    if not rules:
        return ["Rules file cannot be empty - at least one rule must be defined"]

    for rule_num, rule in enumerate(rules, 1):
        if not isinstance(rule, dict):
            errors.append(f"Rule #{rule_num}: Must be a dictionary, got {type(rule).__name__}")
            continue

        # Validate optional name field
        name = rule.get("name")
        if name is not None:
            if not isinstance(name, str):
                errors.append(f"Rule #{rule_num}: 'name' must be a string, got {type(name).__name__}")
            elif len(name.strip()) == 0:
                errors.append(f"Rule #{rule_num}: 'name' cannot be empty")
            elif len(name) > 200:
                errors.append(f"Rule #{rule_num}: 'name' too long ({len(name)} chars, max 200)")

        # Validate optional description field
        description = rule.get("description")
        if description is not None:
            if not isinstance(description, str):
                errors.append(f"Rule #{rule_num}: 'description' must be a string, got {type(description).__name__}")
            elif len(description) > 1000:
                errors.append(f"Rule #{rule_num}: 'description' too long ({len(description)} chars, max 1000)")

        # Validate conditions
        conditions = rule.get("conditions", {})
        if not isinstance(conditions, dict):
            errors.append(f"Rule #{rule_num}: 'conditions' must be a dictionary, got {type(conditions).__name__}")
            continue

        if not conditions:
            errors.append(f"Rule #{rule_num}: Rule must contain at least one condition")

        for key, value in conditions.items():
            if key not in VALID_CONDITIONS:
                errors.append(f"Rule #{rule_num}: Invalid condition '{key}' - valid options: {', '.join(VALID_CONDITIONS)}")
                continue

            if value is None or value == "":
                errors.append(f"Rule #{rule_num}: Condition '{key}' cannot have empty value")
                continue

            errors.extend(_validate_condition(rule_num, key, value))

        # Validate case_sensitive
        case_sensitive = rule.get("case_sensitive")
        if case_sensitive is not None and not isinstance(case_sensitive, bool):
            errors.append(f"Rule #{rule_num}: 'case_sensitive' must be boolean, got {type(case_sensitive).__name__}")

        # Validate action
        action = rule.get("action")
        if not action:
            errors.append(f"Rule #{rule_num}: Rule must contain 'action' field")
        elif not isinstance(action, dict):
            errors.append(f"Rule #{rule_num}: 'action' must be a dictionary, got {type(action).__name__}")
        else:
            errors.extend(_validate_action(rule_num, action))

        # Validate check_archive
        check_archive = rule.get("check_archive")
        if check_archive is not None and not isinstance(check_archive, bool):
            errors.append(f"Rule #{rule_num}: 'check_archive' must be boolean, got {type(check_archive).__name__}")

        # Validate is_directory
        is_directory = rule.get("is_directory")
        if is_directory is not None and not isinstance(is_directory, bool):
            errors.append(f"Rule #{rule_num}: 'is_directory' must be boolean, got {type(is_directory).__name__}")

    if errors:
        logger.error("Rules validation failed with %d errors:", len(errors))
        for error in errors:
            logger.error("• %s", error)

    return errors
