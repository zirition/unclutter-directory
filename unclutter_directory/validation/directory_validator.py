import os
from typing import List

from ..config.organize_config import OrganizeConfig
from .base import Validator


class DirectoryValidator(Validator):
    """Validates target directory permissions and accessibility"""

    def validate(self, config: OrganizeConfig) -> List[str]:
        """
        Validate that target directory exists and is accessible

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        if not config.target_dir.exists():
            errors.append(f"Target directory {config.target_dir} does not exist")
            return errors  # No point in checking further if directory doesn't exist

        if not config.target_dir.is_dir():
            errors.append(f"Target path {config.target_dir} is not a directory")
            return errors

        # Check permissions
        if not os.access(config.target_dir, os.R_OK):
            errors.append(f"No read permission for directory {config.target_dir}")

        if not os.access(config.target_dir, os.W_OK):
            errors.append(f"No write permission for directory {config.target_dir}")

        return errors
