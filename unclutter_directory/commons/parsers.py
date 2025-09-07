import re

SIZE_UNITS = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
TIME_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def parse_size(size_str: str) -> int:
    """
    Parse human-readable size string to bytes.

    Args:
        size_str: Size string in formats like "1024", "1KB", "2.5GB", etc.
                  Supports units: B, KB, MB, GB (case-insensitive)

    Returns:
        int: Number of bytes

    Raises:
        ValueError: If format is invalid or unit is unknown

    Examples:
        >>> parse_size("1024")
        1024
        >>> parse_size("1KB")
        1024
        >>> parse_size("500MB")
        524288000
        >>> parse_size("invalid")
        ValueError: Size parsing failed: Invalid size format: 'invalid'
    """
    try:
        # Strip whitespace and match pattern
        size_str = size_str.strip()
        match = re.fullmatch(r"(\d+(\.\d+)?)\s*([KMG]?B?)?$", size_str, re.IGNORECASE)

        if not match:
            raise ValueError(f"Invalid size format: '{size_str}'")

        groups = match.groups()
        value_str = groups[0]
        unit = groups[2]  # Third group contains the unit
        value = float(value_str)

        # Normalize unit
        if unit:
            unit = unit.upper()
            # Handle cases like "KB", "K", "B"
            if unit.endswith("B"):
                unit = unit[:-1] + "B"  # "KB" -> "KB", "MB" -> "MB"
            elif len(unit) == 1:  # Handle "K", "M", "G"
                unit += "B"
            else:
                unit = "B"
        else:
            unit = "B"

        if unit not in SIZE_UNITS:
            raise ValueError(f"Unsupported size unit: '{unit}'")

        return int(value * SIZE_UNITS[unit])

    except (ValueError, TypeError) as e:
        raise ValueError(f"Failed to parse size '{size_str}': {str(e)}") from e


def parse_time(time_str: str) -> int:
    """
    Parse human-readable time string to seconds.

    Args:
        time_str: Time string in formats like "60", "5m", "2h", "30d", "1w"
                  Supports units: s (seconds), m (minutes), h (hours),
                  d (days), w (weeks)

    Returns:
        int: Number of seconds

    Raises:
        ValueError: If format is invalid or unit is unknown

    Examples:
        >>> parse_time("60")
        60
        >>> parse_time("5m")
        300
        >>> parse_time("2h")
        7200
        >>> parse_time("invalid")
        ValueError: Failed to parse time 'invalid': Invalid time format: 'invalid'
    """
    try:
        time_str = time_str.strip()
        match = re.fullmatch(r"(\d+(\.\d+)?)\s*([smhdw])?$", time_str, re.IGNORECASE)

        if not match:
            raise ValueError(f"Invalid time format: '{time_str}'")

        groups = match.groups()
        value_str = groups[0]
        unit = groups[2]  # Third group contains the unit
        value = float(value_str)

        # Default to seconds if no unit
        unit = unit.lower() if unit else "s"

        if unit not in TIME_UNITS:
            raise ValueError(f"Unsupported time unit: '{unit}'")

        return int(value * TIME_UNITS[unit])

    except (ValueError, TypeError) as e:
        raise ValueError(f"Failed to parse time '{time_str}': {str(e)}") from e
