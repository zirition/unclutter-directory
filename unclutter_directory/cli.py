import sys
from pathlib import Path
from typing import Optional

import click
from click_supercharged import SuperchargedClickGroup

from .commands.delete_unpacked_command import DeleteUnpackedCommand
from .commands.organize_command import OrganizeCommand
from .commons import get_logger
from .config.delete_unpacked_config import DeleteUnpackedConfig
from .config.organize_config import OrganizeConfig
from .validation.rules_validator import RulesFileValidator

logger = get_logger()


@click.group(cls=SuperchargedClickGroup)
def cli():
    """Organize your directories with ease using rule-based file management."""
    pass


@cli.command(default_command=True)
@click.argument(
    "target_dir", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.argument(
    "rules_file", type=click.Path(exists=True, dir_okay=False), required=False
)
@click.option(
    "--dry-run", "-n", is_flag=True, help="Simulate actions without making changes"
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error messages")
@click.option("--always-delete", is_flag=True, help="Delete files without confirmation")
@click.option(
    "--never-delete", is_flag=True, help="Never delete files, skip delete actions"
)
@click.option(
    "--include-hidden", is_flag=True, help="Process hidden files and directories"
)
def organize(
    target_dir: Path,
    rules_file: Optional[str],
    dry_run: bool,
    quiet: bool,
    always_delete: bool,
    never_delete: bool,
    include_hidden: bool,
) -> None:
    """
    Organize files in TARGET_DIR based on rules from RULES_FILE.

    If no rules file is specified, looks for .unclutter_rules.yaml in the target directory.
    """
    try:
        # Create configuration
        config = OrganizeConfig(
            target_dir=target_dir,
            rules_file=rules_file,
            dry_run=dry_run,
            quiet=quiet,
            always_delete=always_delete,
            never_delete=never_delete,
            include_hidden=include_hidden,
        )

        # Execute organize command
        command = OrganizeCommand(config)
        command.execute()

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


@cli.command(aliases=["check"])
@click.argument("rules_file", type=click.Path(exists=True, dir_okay=False))
def validate(rules_file: str) -> None:
    """
    Validate the structure and content of a rules file.

    Checks for proper YAML format, valid rule structure, and logical consistency.
    """
    try:
        # Create minimal config for validation
        config = OrganizeConfig(
            target_dir=Path.cwd(),  # Dummy directory for validation
            rules_file=rules_file,
            dry_run=False,
            quiet=False,
            always_delete=False,
            never_delete=False,
            include_hidden=False,
        )

        # Validate using rules validator
        validator = RulesFileValidator()
        errors = validator.validate(config)

        if errors:
            logger.error("Validation failed:")
            for error in errors:
                logger.error(f"  • {error}")
            sys.exit(1)
        else:
            logger.info(f"✅ Rules file '{rules_file}' is valid")

    except Exception as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)


@cli.command("delete-unpacked", aliases=["remove-unpacked", "clean-archives"])
@click.argument(
    "target_dir", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option(
    "--always-delete",
    "-y",
    is_flag=True,
    help="Delete duplicate directories without confirmation",
)
@click.option(
    "--never-delete",
    is_flag=True,
    help="Never delete directories, only show potential duplicates",
)
@click.option(
    "--include-hidden",
    is_flag=True,
    help="Include hidden files and directories in comparison",
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error messages")
def delete_unpacked(
    target_dir: Path,
    always_delete: bool,
    never_delete: bool,
    include_hidden: bool,
    quiet: bool,
) -> None:
    """
    Remove uncompressed directories that match compressed files.

    Scans TARGET_DIR for compressed files (ZIP, RAR) and looks for
    directories with the same name (without extension). If they exist
    and have identical file structures, prompts to remove the uncompressed directory.

    By default, runs in interactive mode.
    """
    try:
        # Validate conflicting options
        if always_delete and never_delete:
            logger.error("--always-delete and --never-delete are mutually exclusive")
            sys.exit(1)

        # Create configuration
        config = DeleteUnpackedConfig(
            target_dir=target_dir,
            always_delete=always_delete,
            never_delete=never_delete,
            include_hidden=include_hidden,
            quiet=quiet,
        )

        # Execute check duplicates command
        command = DeleteUnpackedCommand(config)
        command.execute()

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
