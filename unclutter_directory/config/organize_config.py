from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class ExecutionMode(Enum):
    """Execution mode for organize operation"""
    DRY_RUN = "dry_run"
    INTERACTIVE = "interactive"
    AUTOMATIC = "automatic"


@dataclass
class OrganizeConfig:
    """Configuration object for organize operation"""
    target_dir: Path
    rules_file: Optional[str]
    dry_run: bool
    quiet: bool
    always_delete: bool
    never_delete: bool
    include_hidden: bool
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.always_delete and self.never_delete:
            raise ValueError("always_delete and never_delete are mutually exclusive")
    
    @property
    def execution_mode(self) -> ExecutionMode:
        """Determine execution mode based on configuration"""
        if self.dry_run:
            return ExecutionMode.DRY_RUN
        elif self.always_delete or self.never_delete:
            return ExecutionMode.AUTOMATIC
        else:
            return ExecutionMode.INTERACTIVE
    
    @property
    def rules_file_path(self) -> Optional[Path]:
        """Get rules file as Path object"""
        return Path(self.rules_file) if self.rules_file else None