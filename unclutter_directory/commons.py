import sys
import re
import logging
from typing import List, Dict


# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("unclutter_directory")

def get_logger():
    return logger

# Constants for validation
VALID_CONDITIONS = {
    "start", "end", "contain", "regex",
    "larger", "smaller", "older", "newer"
}
VALID_ACTIONS = {"move", "delete", "compress"}
SIZE_UNITS = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
TIME_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}

def parse_size(size_str: str) -> int:
    """Parse human-readable size string to bytes."""
    try:
        match = re.fullmatch(r"\s*(\d+)\s*([KMG]?B?|B)\s*", size_str, re.IGNORECASE)
        if not match:
            raise ValueError(f"Invalid size format: '{size_str}'")
            
        value, unit = match.groups()
        unit = unit.upper().replace("B", "") + "B" if unit else "B"
        unit = "B" if unit == "B" else unit  # Handle standalone 'B'
        
        if unit not in SIZE_UNITS:
            raise ValueError(f"Unsupported size unit: '{unit}'")
            
        return int(value) * SIZE_UNITS[unit]
    except (ValueError, TypeError) as e:
        raise ValueError(f"Size parsing failed: {str(e)}") from e

def parse_time(time_str: str) -> int:
    """Parse human-readable time string to seconds."""
    try:
        match = re.fullmatch(r"\s*(\d+)\s*([smhdw]?)\s*", time_str, re.IGNORECASE)
        if not match:
            raise ValueError(f"Invalid time format: '{time_str}'")
            
        value, unit = match.groups()
        unit = unit.lower() if unit else "s"
        
        if unit not in TIME_UNITS:
            raise ValueError(f"Unsupported time unit: '{unit}'")
            
        return int(value) * TIME_UNITS[unit]
    except (ValueError, TypeError) as e:
        raise ValueError(f"Time parsing failed: {str(e)}") from e

def _validate_condition(rule_num: int, key: str, value: str) -> List[str]:
    """Validate individual condition key-value pair."""
    errors = []
    
    if key in {"larger", "smaller"}:
        try:
            parse_size(value)
        except ValueError as e:
            errors.append(f"Rule #{rule_num}: Invalid size value '{value}' for '{key}' - {str(e)}")
            
    elif key in {"older", "newer"}:
        try:
            parse_time(value)
        except ValueError as e:
            errors.append(f"Rule #{rule_num}: Invalid time value '{value}' for '{key}' - {str(e)}")
            
    elif key == "regex":
        try:
            re.compile(value)
        except re.error as e:
            errors.append(f"Rule #{rule_num}: Invalid regex pattern '{value}' - {str(e)}")
            
    return errors

def _validate_action(rule_num: int, action: Dict) -> List[str]:
    """Validate action dictionary."""
    errors = []
    action_type = action.get("type")
    
    if not action_type:
        errors.append(f"Rule #{rule_num}: Action missing required 'type' field")
    elif action_type not in VALID_ACTIONS:
        errors.append(f"Rule #{rule_num}: Invalid action type '{action_type}'")
    elif action_type in ["move", "compress"] and not action.get("target"):
        errors.append(f"Rule #{rule_num}: '{action_type}' action requires 'target' parameter")
        
    if action.get("target") and not isinstance(action["target"], str):
        errors.append(f"Rule #{rule_num}: Target must be a string")
        
    return errors

def validate_rules_file(rules: List) -> List[str]:
    """Validate complete rules file structure and contents."""
    errors = []
    
    if not isinstance(rules, list):
        return ["Rules file must be a list of rule dictionaries"]
        
    for rule_num, rule in enumerate(rules, 1):
        if not isinstance(rule, dict):
            errors.append(f"Rule #{rule_num}: Must be a dictionary")
            continue
            
        # Validate conditions
        conditions = rule.get("conditions", {})
        if not isinstance(conditions, dict):
            errors.append(f"Rule #{rule_num}: 'conditions' must be a dictionary")
            continue
            
        for key, value in conditions.items():
            if key not in VALID_CONDITIONS:
                errors.append(f"Rule #{rule_num}: Invalid condition '{key}'")
                continue
                
            errors.extend(_validate_condition(rule_num, key, value))
            
        # Validate case sensitivity
        case_sensitive = rule.get("case_sensitive")
        if case_sensitive is not None and not isinstance(case_sensitive, bool):
            errors.append(f"Rule #{rule_num}: 'case_sensitive' must be boolean")
            
        # Validate action
        action = rule.get("action", {})
        if not isinstance(action, dict):
            errors.append(f"Rule #{rule_num}: 'action' must be a dictionary")
        else:
            errors.extend(_validate_action(rule_num, action))
            
        # Validate check_archive
        check_archive = rule.get("check_archive")
        if check_archive is not None and not isinstance(check_archive, bool):
            errors.append(f"Rule #{rule_num}: 'check_archive' must be boolean")
            
        # Validate is_directory
        is_directory = rule.get("is_directory")
        if is_directory is not None and not isinstance(is_directory, bool):
            errors.append(f"Rule #{rule_num}: 'is_directory' must be boolean")

    if errors:
        logger.error("Validation failed with %d errors:", len(errors))
        for error in errors:
            logger.error("• %s", error)
            
    return errors