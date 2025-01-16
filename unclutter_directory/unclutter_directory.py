import os
import logging
import click
import yaml

from .FileMatcher import FileMatcher
from .File import File
from .ActionExecutor import ActionExecutor
from .commons import is_valid_rules_file

from pathlib import Path



# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("download_organizer")


def _load_rules(rules_file):
    with open(rules_file, "r") as f:
        try:
            rules = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Error loading YAML: {e}")
            return

    return rules



# CLI with Click
@click.group()
def cli():
    "Organize your directories with ease."
    pass


@cli.command()
@click.argument("rules_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("target_dir", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Simulate the actions without making changes.",
)
def organize(rules_file, target_dir, dry_run):
    "Organize files in directory based on the file rules."

    rules = _load_rules(rules_file)

    # Check if rules file is valid
    if is_valid_rules_file(rules):
        logger.error("Invalid rules file")
        return

    matcher = FileMatcher(rules)

    # Traverse directory
    for root, _, files in os.walk(target_dir):
        for file_name in files:
            file_path = Path(root) / file_name
            file = File.from_path(file_path)
            rule = matcher.match(file)

            if not rule:
                continue

            action = rule.get("action", {})
            action_type = action.get("type")
            logger.info(
                f"Matched file: {file_path} | Action: {action_type} | Target: {action.get('target')}"
            )
            if dry_run:
                continue

            executor = ActionExecutor(action)
            executor.execute_action(file_path)


@cli.command()
@click.argument("rules_file", type=click.Path(exists=True, dir_okay=False))
def validate(rules_file):
    "Validate the structure and attributes of a RULES_FILE."

    rules = _load_rules(rules_file)

    is_valid_rules_file(rules)
    logger.info("Validation complete.")

if __name__ == "__main__":
    cli()

