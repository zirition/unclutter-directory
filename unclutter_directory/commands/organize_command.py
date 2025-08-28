import logging
import sys
from typing import Dict

from ..config.organize_config import OrganizeConfig
from ..validation.validation_chain import ValidationChain
from ..factories.component_factory import ComponentFactory
from ..execution.file_processor import FileProcessor
from ..execution.strategies import RuleResponses
from ..commons import validations

logger = validations.get_logger()


class OrganizeCommand:
    """
    Main command orchestrator for the organize operation.
    Coordinates validation, component creation, and file processing.
    """
    
    def __init__(self, config: OrganizeConfig):
        """
        Initialize organize command
        
        Args:
            config: Configuration for the organize operation
        """
        self.config = config
        self.validation_chain = ValidationChain()
        self.factory = ComponentFactory()
        self.rule_responses: RuleResponses = {}
    
    def execute(self) -> None:
        """
        Execute the organize operation following the complete workflow:
        1. Setup logging
        2. Validate configuration
        3. Process files
        """
        try:
            self._setup_logging()
            self._validate_config()
            self._process_files()
        except KeyboardInterrupt:
            logger.info("\nOperation cancelled by user")
        except Exception as e:
            logger.error(f"Unexpected error during organize operation: {e}")
            raise
    
    def _setup_logging(self) -> None:
        """Configure logging based on configuration"""
        level = logging.ERROR if self.config.quiet else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(message)s",
            handlers=[logging.StreamHandler()]
        )
    
    def _validate_config(self) -> None:
        """Validate configuration and exit if invalid"""
        errors = self.validation_chain.validate(self.config)
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  • {error}")
            sys.exit(1)
    
    def _process_files(self) -> None:
        """Process all files in target directory"""
        try:
            # Create components using factory
            collector = self.factory.create_file_collector(self.config)
            matcher = self.factory.create_file_matcher(self.config)
            strategy = self.factory.create_execution_strategy(self.config)
            
            # Collect files to process
            files = collector.collect(
                self.config.target_dir, 
                self.config.rules_file_path
            )
            
            if not files:
                logger.info("No files found to process")
                return
            
            # Process files
            processor = FileProcessor(matcher, strategy, self.rule_responses)
            stats = processor.process_files(files, self.config.target_dir)
            
            # Log summary statistics
            self._log_processing_summary(stats)
            
        except Exception as e:
            logger.error(f"Error during file processing: {e}")
            raise
    
    def _log_processing_summary(self, stats: Dict[str, int]) -> None:
        """Log processing summary statistics"""
        total = stats["total_files"]
        processed = stats["processed_files"]
        skipped = stats["skipped_files"]
        errors = stats["errors"]
        
        if self.config.dry_run:
            logger.info(f"Dry run completed: {processed}/{total} files would be processed")
        else:
            logger.info(f"Processing completed: {processed}/{total} files processed")
        
        if skipped > 0:
            logger.info(f"  • {skipped} files skipped (no matching rules)")
        if errors > 0:
            logger.warning(f"  • {errors} files had errors during processing")