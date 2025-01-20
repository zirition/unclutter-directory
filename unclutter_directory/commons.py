import sys
import re
from typing import List
import logging


# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("download_organizer")

def get_logger():
    return logger

def parse_size(size_str: str) -> int:
    # Convert size string to bytes
    size_map = {"KB": 1024, "MB": 1024**2, "GB": 1024**3, "B": 1}
    for unit, multiplier in size_map.items():
        if size_str.upper().endswith(unit):
            return int(size_str[: -len(unit)].strip()) * multiplier
    return int(size_str)

def parse_time(time_str: str) -> int:
    # Convert time string to seconds
    time_map = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    for unit, multiplier in time_map.items():
        if time_str.lower().endswith(unit):
            return int(time_str[: -len(unit)].strip()) * multiplier
    return int(time_str)

def is_valid_rules_file(rules) -> List[str]:
    def is_valid_size(value):
        try:
            parse_size(value)
            return True
        except ValueError:
            return False

    def is_valid_time(value):
        try:
            parse_time(value)
            return True
        except ValueError:
            return False

    valid_conditions = {
        "start",
        "end",
        "contain",
        "regex",
        "larger",
        "smaller",
        "older",
        "newer",
    }
    valid_types = {"move", "delete", "compress"}

    errors = []

    if not isinstance(rules, list):
        errors.append("Rules file must be a list of rules.")
        return errors

    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append(f"Rule #{i + 1} must be a dictionary.")
            continue

        # Validate conditions
        conditions = rule.get("conditions", {})
        if not isinstance(conditions, dict):
            errors.append(f"Rule #{i + 1}: 'conditions' must be a dictionary.")
        else:
            for key, value in conditions.items():
                if key not in valid_conditions:
                    errors.append(f"Rule #{i + 1}: Invalid condition '{key}'.")
                elif key in {"larger", "smaller"} and not is_valid_size(value):
                    errors.append(
                        f"Rule #{i + 1}: Invalid size value '{value}' for condition '{key}'."
                    )
                elif key in {"older", "newer"} and not is_valid_time(value):
                    errors.append(
                        f"Rule #{i + 1}: Invalid time value '{value}' for condition '{key}'."
                    )
                elif key == "regex":
                    try:
                        re.compile(value)
                    except re.error:
                        errors.append(
                            f"Rule #{i + 1}: Invalid regular expression '{value}'."
                        )

        # Validate case_sensitive attribute
        case_sensitive = rule.get("case_sensitive")
        if case_sensitive is not None and not isinstance(case_sensitive, bool):
            errors.append(f"Rule #{i + 1}: 'case_sensitive' must be a boolean (True or False).")

        # Validate action
        action = rule.get("action", {})
        if not isinstance(action, dict):
            errors.append(f"Rule #{i + 1}: 'action' must be a dictionary.")
        else:
            action_type = action.get("type")
            if action_type not in valid_types:
                errors.append(f"Rule #{i + 1}: Invalid action type '{action_type}'.")
            if action_type == "move" and not action.get("target"):
                errors.append(f"Rule #{i + 1}: 'move' action requires a 'target'.")

        # Validate check_archive
        if "check_archive" in rule and not isinstance(rule["check_archive"], bool):
            errors.append(f"Rule #{i + 1}: 'check_archive' must be a boolean.")

    # Report errors or success
    if errors:
        logger.error("❌ Validation failed with the following errors:")
        for error in errors:
            logger.error(f"- {error}")

    return errors

