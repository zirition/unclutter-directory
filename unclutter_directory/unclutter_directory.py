import logging
import click
import yaml

from unclutter_directory.UnclutterClickGroup import UnclutterClickGroup

from .FileMatcher import FileMatcher
from .File import File
from .ActionExecutor import ActionExecutor
from .commons import is_valid_rules_file

from pathlib import Path

from unclutter_directory import commons

logger = commons.get_logger()


def _load_rules(rules_file):
    """
    Load rules from a YAML file.
    """
    with open(rules_file, "r") as f:
        try:
            rules = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"❌ Error loading YAML: {e}")
            return

    return rules


def prompt_user_for_action(file_path):
    """
    Prompt the user for an action if the rule is 'delete'.
    """
    valid_responses = {"y": "Yes", "n": "No", "a": "All", "never": "Never"}

    while True:
        response = (
            input(f"Do you want to delete {file_path}? [Y(es)/N(o)/A(ll)/Never]: ")
            .strip()
            .lower()
        )
        if not response:
            response = "y"  # Default to Yes
        if response in valid_responses:
            break
        print("Invalid option. Please choose Y(es), N(o), A(ll), or Never.")

    return response


def check_if_should_delete(rule, rule_responses, file_path):
    """
    Check if the file should be deleted.
    """
    rule_id = id(rule)
    if rule_id in rule_responses:
        user_response = rule_responses[rule_id]
    else:
        user_response = prompt_user_for_action(file_path)

    if user_response == "n":
        return False
    elif user_response == "never":
        rule_responses[rule_id] = "n"
        return False
    elif user_response == "a":
        rule_responses[rule_id] = "y"  # Automatically delete all
        return True
    elif user_response == "y":
        return True


# CLI with Click
@click.group(cls=UnclutterClickGroup)
def cli():
    "Organize your directories with ease."
    pass


@cli.command(default_command=True)
@click.argument("target_dir", type=click.Path(exists=True, file_okay=False))
@click.argument(
    "rules_file", type=click.Path(exists=True, dir_okay=False), required=False
)
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    default=False,
    help="Simulate the actions without making changes.",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Suppress non-error messages.",
)
@click.option(
    "--always-delete",
    is_flag=True,
    default=False,
    help="Always delete matched files without asking.",
)
@click.option(
    "--never-delete",
    is_flag=True,
    default=False,
    help="Never delete matched files.",
)
@click.option(
    "--include-hidden",
    is_flag=True,
    default=False,
    help="Include hidden files (files starting with dot).",
)
def organize(
    target_dir, rules_file, dry_run, quiet, always_delete, never_delete, include_hidden
):
    "Organize files in directory based on the file rules. (Default)"

    # Configure logging
    log_level = logging.ERROR if quiet else logging.INFO
    logging.basicConfig(level=log_level)

    # Validate that --always-delete and --never-delete are not both set
    if always_delete and never_delete:
        logger.error(
            "❌ Options --always-delete and --never-delete are mutually exclusive."
        )
        return

    if not rules_file:
        default_rules = Path(target_dir) / ".unclutter_rules.yaml"
        if default_rules.exists():
            rules_file = str(default_rules)
        else:
            logger.error(
                "❌ No rules file specified and no .unclutter_rules.yaml found in target directory"
            )
            return

    rules = _load_rules(rules_file)

    # Check if rules file is valid
    if is_valid_rules_file(rules):
        logger.error("❌ Invalid rules file")
        return

    matcher = FileMatcher(rules)

    rule_responses = {}

    # Traverse directory, optionally including hidden files
    files = [
        f.name
        for f in Path(target_dir).iterdir()
        if f.is_file() and (include_hidden or not f.name.startswith("."))
    ]

    # Ignore rules file
    if Path(target_dir) == Path(rules_file).parent:
        rules_file_path = Path(rules_file)
        files = [f for f in files if f != rules_file_path.name]

    for file_name in files:
        file_path = Path(target_dir) / file_name
        file = File.from_path(file_path)
        rule = matcher.match(file)

        if not rule:
            continue

        action = rule.get("action", {})
        action_type = action.get("type")
        target_info = (
            f" | Target: {action.get('target')}" if action_type == "move" else ""
        )
        logger.info(f"Matched file: {file_path} | Action: {action_type}{target_info}")
        if dry_run:
            continue

        if action_type == "delete":
            if never_delete:
                logger.info(f"Skipping deletion of {file_path}")
                continue
            if not always_delete and not check_if_should_delete(
                rule, rule_responses, file_path
            ):
                continue

        executor = ActionExecutor(action)
        executor.execute_action(file_path, target_dir)


@cli.command(aliases=["check"])
@click.argument("rules_file", type=click.Path(exists=True, dir_okay=False))
def validate(rules_file):
    "Validate the structure and attributes of a RULES_FILE."

    rules = _load_rules(rules_file)

    is_valid_rules_file(rules)
    logger.info("Validation complete.")


if __name__ == "__main__":
    cli()
