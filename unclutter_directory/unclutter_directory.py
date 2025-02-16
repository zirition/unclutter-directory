import logging
from pathlib import Path
from typing import Dict, List, Optional

import click
import yaml
from click_supercharged import SuperchargedClickGroup

from unclutter_directory import commons
from .ActionExecutor import ActionExecutor
from .File import File
from .FileMatcher import FileMatcher
from .commons import validate_rules_file

logger = commons.get_logger()

# Type aliases for clarity
Rule = Dict
Rules = List[Rule]
RuleResponses = Dict[int, str]


def _load_rules(rules_file: str) -> Optional[Rules]:
    """Load and return rules from a YAML file."""
    try:
        with open(rules_file, "r") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"❌ Error loading YAML: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error reading rules file: {e}")
    return None


def _collect_files(target_dir: Path, include_hidden: bool) -> List[Path]:
    """Collect files and directories to process"""
    return [
        f for f in target_dir.iterdir()
        if (include_hidden or not f.name.startswith("."))
    ]


def _should_exclude_rules_file(file_path: Path, rules_file: Path, target_dir: Path) -> bool:
    """Check if a file should be excluded from processing."""
    return target_dir == rules_file.parent and file_path == rules_file


def _handle_deletion(
    file_path: Path,
    rule: Rule,
    rule_responses: RuleResponses,
    always_delete: bool,
    never_delete: bool
) -> bool:
    """Determine if a file should be deleted based on user preferences and history."""
    if never_delete:
        logger.info(f"Skipping deletion of {file_path}")
        return False
    if always_delete:
        return True

    rule_id = id(rule)
    response = rule_responses.get(rule_id, prompt_user_for_action(file_path))
    
    if response == "a":
        rule_responses[rule_id] = "y"
        return True
    if response == "never":
        rule_responses[rule_id] = "n"
        return False
        
    return response == "y"


def _process_file(
    file_path: Path,
    target_dir: Path,
    matcher: FileMatcher,
    dry_run: bool,
    rule_responses: RuleResponses,
    always_delete: bool,
    never_delete: bool
) -> None:
    """Process an individual file according to matched rules."""
    file = File.from_path(file_path)
    if not (rule := matcher.match(file)):
        return

    action = rule.get("action", {})
    action_type = action.get("type")
    target_info = f" | Target: {action.get('target')}" if action_type == "move" else ""
    
    logger.info(f"Matched file: {file_path} | Action: {action_type}{target_info}")
    if dry_run:
        return

    if action_type == "delete":
        if not _handle_deletion(file_path, rule, rule_responses, always_delete, never_delete):
            return

    ActionExecutor(action).execute_action(file_path, target_dir)


def _validate_rules(rules_file: str) -> bool:
    """Validate rules file and return success status."""
    if not (rules := _load_rules(rules_file)):
        return False
    
    if errors := validate_rules_file(rules):
        logger.error("❌ Validation failed with %d errors:", len(errors))
        for error in errors:
            logger.error("• %s", error)
        return False
    return True


def prompt_user_for_action(file_path: Path) -> str:
    """Prompt user for deletion confirmation and return normalized response."""
    valid_responses = {"y", "n", "a", "never"}
    prompt = f"Do you want to delete {file_path}? [Y(es)/N(o)/A(ll)/Never]: "

    while True:
        response = input(prompt).strip().lower() or "y"
        if response in valid_responses:
            return response
        print("Invalid option. Please choose Y(es), N(o), A(ll), or Never.")


@click.group(cls=SuperchargedClickGroup)
def cli():
    """Organize your directories with ease."""
    pass


@cli.command(default_command=True)
@click.argument("target_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("rules_file", type=click.Path(exists=True, dir_okay=False), required=False)
@click.option("--dry-run", "-n", is_flag=True, help="Simulate actions without changes")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error messages")
@click.option("--always-delete", is_flag=True, help="Delete without confirmation")
@click.option("--never-delete", is_flag=True, help="Never delete files")
@click.option("--include-hidden", is_flag=True, help="Process hidden files")
def organize(
    target_dir: Path,
    rules_file: Optional[str],
    dry_run: bool,
    quiet: bool,
    always_delete: bool,
    never_delete: bool,
    include_hidden: bool
) -> None:
    """Organize files based on rules."""
    logging.basicConfig(level=logging.ERROR if quiet else logging.INFO)

    if always_delete and never_delete:
        logger.error("❌ --always-delete and --never-delete are mutually exclusive")
        click.exit(code=1)

    # Resolve default rules file if not specified
    if not rules_file and (default_rules := target_dir / ".unclutter_rules.yaml").exists():
        rules_file = str(default_rules)
    
    if not rules_file or not (rules := _load_rules(rules_file)):
        logger.error("❌ No valid rules file specified")
        click.exit(code=1)

    if validate_rules_file(rules):
        click.exit(code=1) # Validation errors already logged

    matcher = FileMatcher(rules)
    rule_responses: RuleResponses = {}
    rules_file_path = Path(rules_file)

    try:
        files = _collect_files(target_dir, include_hidden)
        files = [f for f in files if not _should_exclude_rules_file(f, rules_file_path, target_dir)]

        for file_path in files:
            _process_file(
                file_path,
                target_dir,
                matcher,
                dry_run,
                rule_responses,
                always_delete,
                never_delete
            )
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")


@cli.command(aliases=["check"])
@click.argument("rules_file", type=click.Path(exists=True, dir_okay=False))
def validate(rules_file: str) -> None:
    """Validate a rules file."""
    if _validate_rules(rules_file):
        logger.info("✅ Rules file is valid")


if __name__ == "__main__":
    cli()