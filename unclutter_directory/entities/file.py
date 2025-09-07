import calendar
from datetime import datetime
from pathlib import Path

from unclutter_directory.commons import get_logger

logger = get_logger()


class File:
    def __init__(
        self, path: Path, name: str, date: float, size: int, is_directory: bool = False
    ):
        self.path = path
        self.name = name
        if isinstance(date, tuple):
            date = self._normalize_date_tuple(date)
        self.date = date
        self.size = size
        self.is_directory = is_directory

    @staticmethod
    def _normalize_date_tuple(date_tuple):
        """Normalize a date tuple by correcting invalid components, focusing on days outside the month range.

        - Underflow (day < 1): Subtract from previous month (e.g., day 0 in January -> day 31 of previous December).
        - Overflow (day > days in month): Add to next month (e.g., day 32 in April -> day 2 of May).
        - Clamp other components to valid ranges.
        - Return timestamp of the normalized date.
        """
        year = date_tuple[0]
        month = date_tuple[1] if len(date_tuple) > 1 else 1
        day = date_tuple[2] if len(date_tuple) > 2 else 1
        hour = date_tuple[3] if len(date_tuple) > 3 else 0
        minute = date_tuple[4] if len(date_tuple) > 4 else 0
        second = date_tuple[5] if len(date_tuple) > 5 else 0

        # Clamp components except day (will be normalized separately)
        year = max(1970, min(year, 9999))  # Clamp to safe range for timestamp
        month = max(1, min(month, 12))
        hour = max(0, min(hour, 23))
        minute = max(0, min(minute, 59))
        second = max(0, min(second, 59))

        # Normalize day handling underflow and overflow
        while day < 1:
            month -= 1
            if month == 0:
                month = 12
                year -= 1
                year = max(1970, year)  # Ensure year doesn't go below safe range
            days_in_prev_month = calendar.monthrange(year, month)[1]
            day += days_in_prev_month

        while day > calendar.monthrange(year, month)[1]:
            days_in_month = calendar.monthrange(year, month)[1]
            day -= days_in_month
            month += 1
            if month > 12:
                month = 1
                year += 1

        # Create and return timestamp
        try:
            return datetime(year, month, day, hour, minute, second).timestamp()
        except ValueError as e:
            # Raise the exception instead of fallback
            logger.error(f"Invalid date after normalization: {year}-{month}-{day} {hour}:{minute}:{second}. Original error: {e}")
            raise ValueError(f"Unable to create valid datetime after normalization: {year}-{month}-{day} {hour}:{minute}:{second}") from e

    @staticmethod
    def from_path(file_path: Path):
        if file_path.is_dir():
            total_size = 0
            latest_mtime = 0
            for child in file_path.rglob("*"):
                if child.is_file():
                    total_size += child.stat().st_size
                    child_mtime = child.stat().st_mtime
                    latest_mtime = max(latest_mtime, child_mtime)
            return File(
                file_path.parent,
                file_path.name,
                latest_mtime,
                total_size,
                is_directory=True,
            )
        else:
            stats = file_path.stat()
            return File(
                file_path.parent,
                file_path.name,
                stats.st_mtime,
                stats.st_size,
                is_directory=False,
            )
