import re
from typing import Any, Dict, List

from unclutter_directory.commons.logging import logger
from unclutter_directory.commons.parsers import parse_size, parse_time

# Type aliases
Rules = List[dict]
# Constants for validation
VALID_CONDITIONS = {
    "start",
    "end",
    "contain",
    "regex",
    "larger",
    "smaller",
    "older",
    "newer",
}
VALID_ACTIONS = {"move", "delete", "compress"}


def _get_rule_identifier(rule_num: int, rule: dict) -> str:
    """
    Get rule identifier for error reporting.

    Returns rule name if available and valid, otherwise returns rule number.

    Args:
        rule_num: Rule number (1-based index)
        rule: Rule dictionary

    Returns:
        Rule identifier as string
    """
    # Check if rule is a dictionary before trying to access its properties
    if not isinstance(rule, dict):
        return f"#{rule_num}"

    name = rule.get("name")
    if name is not None and isinstance(name, str) and len(name.strip()) > 0:
        return name
    return f"#{rule_num}"


def _validate_condition(rule_num: int, key: str, value: str, rule: dict) -> List[str]:
    """
    Validate individual condition key-value pair.

    Args:
        rule_num: Rule number for error reporting
        key: Condition name (start, end, contain, regex, larger, smaller, older, newer)
        value: Condition value as string
        rule: Rule dictionary for identifier resolution

    Returns:
        List[str]: List of validation errors (empty if valid)

    Note:
        This function validates individual condition values without checking
        if the condition key itself is valid (that's handled elsewhere).
    """
    errors = []
    rule_id = _get_rule_identifier(rule_num, rule)

    if key in {"larger", "smaller"}:
        try:
            parse_size(value)
        except ValueError as e:
            errors.append(
                f"Rule {rule_id}: Invalid size value '{value}' for '{key}' - {e}"
            )

    elif key in {"older", "newer"}:
        try:
            parse_time(value)
        except ValueError as e:
            errors.append(
                f"Rule {rule_id}: Invalid time value '{value}' for '{key}' - {e}"
            )

    elif key == "regex":
        try:
            re.compile(value)
        except re.error as e:
            errors.append(f"Rule {rule_id}: Invalid regex pattern '{value}' - {e}")

    return errors


def _validate_action(rule_num: int, action: Dict[str, Any], rule: dict) -> List[str]:
    """
    Validate action dictionary from a rule.

    Args:
        rule_num: Rule number for error reporting
        action: Action dictionary with 'type' and optional 'target'
        rule: Rule dictionary for identifier resolution

    Returns:
        List[str]: List of validation errors (empty if valid)

    Examples:
        Valid actions:
        - {"type": "move", "target": "/path/to/dest"}
        - {"type": "delete"}
        - {"type": "compress", "target": "."}
    """
    errors = []
    rule_id = _get_rule_identifier(rule_num, rule)
    action_type = action.get("type")

    if not action_type:
        errors.append(f"Rule {rule_id}: Action missing required 'type' field")
    elif action_type not in VALID_ACTIONS:
        errors.append(
            f"Rule {rule_id}: Invalid action type '{action_type}' - valid options: {', '.join(VALID_ACTIONS)}"
        )
    elif action_type in ["move", "compress"] and not action.get("target"):
        errors.append(
            f"Rule {rule_id}: '{action_type}' action requires 'target' parameter"
        )

    target = action.get("target")
    if target and not isinstance(target, str):
        errors.append(
            f"Rule {rule_id}: Target must be a string, got {type(target).__name__}"
        )

    # Validate target path safety (basic check)
    if target and isinstance(target, str):
        if target.startswith("..") or any(
            part in target.split("/") for part in ["../../../..", "...."]
        ):
            errors.append(f"Rule {rule_id}: Target path contains suspicious patterns")

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
        rule_id = _get_rule_identifier(rule_num, rule)

        if not isinstance(rule, dict):
            errors.append(
                f"Rule {rule_id}: Must be a dictionary, got {type(rule).__name__}"
            )
            continue

        # Validate optional name field
        name = rule.get("name")
        if name is not None:
            if not isinstance(name, str):
                errors.append(
                    f"Rule #{rule_num}: 'name' must be a string, got {type(name).__name__}"
                )
            elif len(name.strip()) == 0:
                errors.append(f"Rule #{rule_num}: 'name' cannot be empty")
            elif len(name) > 200:
                errors.append(
                    f"Rule #{rule_num}: 'name' too long ({len(name)} chars, max 200)"
                )

        # Validate optional description field
        description = rule.get("description")
        if description is not None:
            if not isinstance(description, str):
                errors.append(
                    f"Rule {rule_id}: 'description' must be a string, got {type(description).__name__}"
                )
            elif len(description) > 1000:
                errors.append(
                    f"Rule {rule_id}: 'description' too long ({len(description)} chars, max 1000)"
                )

        # Validate conditions
        conditions = rule.get("conditions", {})
        if not isinstance(conditions, dict):
            errors.append(
                f"Rule {rule_id}: 'conditions' must be a dictionary, got {type(conditions).__name__}"
            )
            continue

        if not conditions:
            errors.append(f"Rule {rule_id}: Rule must contain at least one condition")

        for key, value in conditions.items():
            if key not in VALID_CONDITIONS:
                errors.append(
                    f"Rule {rule_id}: Invalid condition '{key}' - valid options: {', '.join(VALID_CONDITIONS)}"
                )
                continue

            if value is None or value == "":
                errors.append(
                    f"Rule {rule_id}: Condition '{key}' cannot have empty value"
                )
                continue

            errors.extend(_validate_condition(rule_num, key, value, rule))

        # Validate case_sensitive
        case_sensitive = rule.get("case_sensitive")
        if case_sensitive is not None and not isinstance(case_sensitive, bool):
            errors.append(
                f"Rule {rule_id}: 'case_sensitive' must be boolean, got {type(case_sensitive).__name__}"
            )

        # Validate action
        action = rule.get("action")
        if not action:
            errors.append(f"Rule {rule_id}: Rule must contain 'action' field")
        elif not isinstance(action, dict):
            errors.append(
                f"Rule {rule_id}: 'action' must be a dictionary, got {type(action).__name__}"
            )
        else:
            errors.extend(_validate_action(rule_num, action, rule))

        # Validate check_archive
        check_archive = rule.get("check_archive")
        if check_archive is not None and not isinstance(check_archive, bool):
            errors.append(
                f"Rule {rule_id}: 'check_archive' must be boolean, got {type(check_archive).__name__}"
            )

        # Validate is_directory
        is_directory = rule.get("is_directory")
        if is_directory is not None and not isinstance(is_directory, bool):
            errors.append(
                f"Rule {rule_id}: 'is_directory' must be boolean, got {type(is_directory).__name__}"
            )

        # Validate delete_unpacked_on_match
        delete_unpacked_on_match = rule.get("delete_unpacked_on_match")
        if delete_unpacked_on_match is not None and not isinstance(
            delete_unpacked_on_match, bool
        ):
            errors.append(
                f"Rule {rule_id}: 'delete_unpacked_on_match' must be boolean, got {type(delete_unpacked_on_match).__name__}"
            )

    if errors:
        logger.error("Rules validation failed with %d errors:", len(errors))
        for error in errors:
            logger.error("• %s", error)

    return errors
