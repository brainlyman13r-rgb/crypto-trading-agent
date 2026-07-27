"""Structured logging configuration."""

import logging
import sys
from pathlib import Path
import structlog
from datetime import datetime


def setup_logging(log_dir: str = "logs", level: str = "INFO"):
    """Configure structured logging with file and console output."""
    
    # Ensure log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(log_dir) / f"trading_agent_{timestamp}.log"
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    handler_file = logging.FileHandler(log_file)
    handler_file.setLevel(getattr(logging, level.upper()))
    
    handler_console = logging.StreamHandler(sys.stdout)
    handler_console.setLevel(getattr(logging, level.upper()))
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler_file.setFormatter(formatter)
    handler_console.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler_file)
    root_logger.addHandler(handler_console)
    root_logger.setLevel(getattr(logging, level.upper()))
    
    logger = structlog.get_logger()
    logger.info("Logging initialized", log_file=str(log_file))
    
    return logger


def get_logger(name: str = __name__):
    """Get a logger instance."""
    return structlog.get_logger(name)
