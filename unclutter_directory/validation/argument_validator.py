from ..config.organize_config import OrganizeConfig
from .base import Validator


class ArgumentValidator(Validator):
    """Validates command line arguments for logical consistency"""

    def validate(self, config: OrganizeConfig) -> list[str]:
        """
        Validate that command line arguments don't conflict with each other

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Check for mutually exclusive delete options
        if config.always_delete and config.never_delete:
            errors.append("--always-delete and --never-delete are mutually exclusive")

        return errors
