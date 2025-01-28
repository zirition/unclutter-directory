import shutil
from typing import Dict
from pathlib import Path
import zipfile

from unclutter_directory import commons

logger = commons.get_logger()

class ActionExecutor:
    def __init__(self, action: Dict):
        self.action = action

    def resolve_conflict(self, target_path: Path) -> Path:
        """Resolve filename conflicts by adding a numerical suffix."""
        if not target_path.exists():
            return target_path

        base_name = target_path.stem
        suffix = 1
        while True:
            new_name = f"{base_name}_{suffix}{target_path.suffix}"
            new_path = target_path.with_name(new_name)
            if not new_path.exists():
                return new_path
            suffix += 1

    def _get_target_directory(self, target: str, parent_path: Path) -> Path:
        """Resolve the target directory path, accounting for absolute/relative paths."""
        target_path = Path(target)
        if target_path.is_absolute():
            return target_path
        else:
            return parent_path / target

    def _handle_move(self, file_path: Path, parent_path: Path, target: str):
        """Handle moving a file to a target directory."""
        rel_path = file_path.relative_to(parent_path)
        target_dir = self._get_target_directory(target, parent_path)
        target_path = target_dir / rel_path
        target_path = self.resolve_conflict(target_path)
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file_path), str(target_path))
        logger.info(f"Moved to {target_path}")

    def _handle_delete(self, file_path: Path):
        """Handle file deletion."""
        try:
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"❌ Error deleting file {file_path}: {e}")

    def _handle_compress(self, file_path: Path, parent_path: Path, target: str):
        """Handle file compression into a target directory."""
        forbidden_extensions = {'.zip', '.rar', '.7z', '.gz', '.bz2', '.tgz', '.xz'}
        if file_path.suffix.lower() in forbidden_extensions:
            logger.info(f"Skipping compression for forbidden file type: {file_path}")
            return

        try:
            target_dir = self._get_target_directory(target, parent_path)
            target_dir.mkdir(parents=True, exist_ok=True)
            
            zip_name = f"{file_path.stem}.zip"
            target_path = target_dir / zip_name
            target_path = self.resolve_conflict(target_path)
            
            with zipfile.ZipFile(target_path, "w") as zipf:
                zipf.write(file_path, arcname=file_path.name)
            logger.info(f"Compressed file: {file_path} to {target_path}")

            file_path.unlink()
        except Exception as e:
            logger.error(f"❌ Error compressing file {file_path}: {e}")

    def execute_action(self, file_path: Path, parent_path: Path):
        action_type = self.action.get("type")
        target = self.action.get("target")

        # Validate action structure
        valid_actions = ["move", "delete", "compress"]
        if not action_type or action_type not in valid_actions:
            logger.warning(f"Invalid action type for file {file_path}")
            return
        if action_type in ["move", "compress"] and not target:
            logger.warning(f"Missing target for {action_type} action on {file_path}")
            return

        try:
            if action_type == "move":
                self._handle_move(file_path, parent_path, Path(target))
            elif action_type == "delete":
                self._handle_delete(file_path)
            elif action_type == "compress":
                self._handle_compress(file_path, parent_path, Path(target))
        except Exception as e:
            logger.error(f"❌ Unexpected error processing {file_path}: {e}")