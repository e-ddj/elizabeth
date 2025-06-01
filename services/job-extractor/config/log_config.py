import logging
import sys
import os

import structlog


def configure_logging():
    # Set log level from environment variable or default to INFO
    log_level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    
    # Configure basic logging to write to stdout
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,  # Override any existing handlers
    )

    # Log the configuration
    logging.info(f"Logging configured with level: {log_level_name}")

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Explicitly set level for root logger and its handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    for handler in root_logger.handlers:
        handler.setLevel(log_level)
    
    # Make sure common libraries don't flood with DEBUG logs
    if log_level > logging.DEBUG:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger():
    return structlog.get_logger()