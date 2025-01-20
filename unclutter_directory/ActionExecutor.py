import os
from typing import Dict
from pathlib import Path
import zipfile

from unclutter_directory import commons

logger = commons.get_logger()

class ActionExecutor:
    def __init__(self, action: Dict):
        self.action = action

    def resolve_conflict(self, target_path: Path) -> Path:
        "Resolve filename conflicts by adding a suffix."
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

    def execute_action(self, file_path: Path, parent_path: Path):
        action_type = self.action.get("type")
        target = self.action.get("target")

        if not action_type or (action_type in ["move"] and not target):
            logger.warning(f"Invalid action for file {file_path}")
            return

        # Execute actions
        if action_type == "move":
            rel_path = file_path.relative_to(parent_path)
            if Path(target).is_absolute():
                target_path = Path(target) / rel_path
            else:
                target_path = Path(parent_path) / target / rel_path
            target_path = self.resolve_conflict(target_path)
            if not target_path:
                logger.error(f"❌ Failed to resolve conflict for {file_path}")
                return
            os.makedirs(target_path.parent, exist_ok=True)
            file_path.rename(target_path)
            logger.info(f"Moved to {target_path}")

        elif action_type == "delete":
            try:
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                logger.error(f"❌ Error deleting file {file_path}: {e}")

        elif action_type == "compress":
            try:
                # Check if the file extension is already one of the compressed archive types
                forbidden_extensions = {'.zip', '.rar', '.7z', '.gz', '.bz2', '.tgz', '.xz'}
                file_extension = file_path.suffix.lower()
                
                if file_extension in forbidden_extensions:
                    logger.info(f"Skipping compression for file with forbidden extension: {file_path}")
                    return

                target_path = Path(target) / f"{file_path.stem}.zip"
                target_path = self.resolve_conflict(target_path)
                with zipfile.ZipFile(target_path, "w") as zipf:
                    zipf.write(file_path, arcname=file_path.name)
                logger.info(f"Compressed file: {file_path} to {target_path}")
            except Exception as e:
                logger.error(f"❌ Error compressing file {file_path}: {e}")

