from abc import ABC, abstractmethod
from typing import List

from ..config.organize_config import OrganizeConfig


class Validator(ABC):
    """Abstract base class for validators in the validation chain"""
    
    @abstractmethod
    def validate(self, config: OrganizeConfig) -> List[str]:
        """
        Validate configuration and return list of error messages.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of error messages, empty if validation passes
        """
        pass