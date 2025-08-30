from typing import List

from ..config.organize_config import OrganizeConfig
from .argument_validator import ArgumentValidator
from .base import Validator
from .directory_validator import DirectoryValidator
from .rules_validator import RulesFileValidator


class ValidationChain:
    """
    Chain of responsibility pattern for validation.
    Runs all validators in sequence and collects all errors.
    """

    def __init__(self):
        """Initialize validation chain with default validators"""
        self.validators: List[Validator] = [
            ArgumentValidator(),
            DirectoryValidator(),
            RulesFileValidator(),  # Must be last as it may modify config
        ]

    def add_validator(self, validator: Validator) -> None:
        """
        Add a custom validator to the chain

        Args:
            validator: Validator instance to add
        """
        self.validators.append(validator)

    def validate(self, config: OrganizeConfig) -> List[str]:
        """
        Run all validators and collect errors

        Args:
            config: Configuration to validate

        Returns:
            List of all validation errors from all validators
        """
        all_errors = []

        for validator in self.validators:
            try:
                errors = validator.validate(config)
                all_errors.extend(errors)
            except Exception as e:
                all_errors.append(
                    f"Validator {validator.__class__.__name__} failed: {e}"
                )

        return all_errors
