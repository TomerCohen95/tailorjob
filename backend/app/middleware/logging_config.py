"""
Logging configuration for sending logs to Loki.
"""
import logging
import os
from logging.handlers import QueueHandler, QueueListener
import queue
import requests
from typing import Optional

class LokiHandler(logging.Handler):
    """
    Simple Loki handler that sends logs via HTTP.
    """
    
    def __init__(self, url: str, labels: Optional[dict] = None):
        super().__init__()
        self.url = url
        self.labels = labels or {}
        self.session = requests.Session()
        
    def emit(self, record: logging.LogRecord):
        """
        Send log record to Loki.
        """
        try:
            # Format the log message
            log_entry = self.format(record)
            
            # Build labels
            labels = {
                "job": "tailorjob-api",
                "level": record.levelname.lower(),
                "logger": record.name,
                **self.labels
            }
            
            # Build Loki payload
            payload = {
                "streams": [
                    {
                        "stream": labels,
                        "values": [
                            [str(int(record.created * 1_000_000_000)), log_entry]
                        ]
                    }
                ]
            }
            
            # Send to Loki
            self.session.post(
                f"{self.url}/loki/api/v1/push",
                json=payload,
                timeout=2
            )
        except Exception as e:
            # Don't let logging errors crash the app
            print(f"Failed to send log to Loki: {e}")


def setup_logging(loki_url: Optional[str] = None):
    """
    Configure logging to send logs to Loki.
    
    Args:
        loki_url: URL of Loki instance (e.g., http://tailorjob-loki.eastus.azurecontainer.io:3100)
    """
    # Get Loki URL from environment if not provided
    if not loki_url:
        loki_url = os.getenv("LOKI_URL")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Loki handler (only if URL is provided)
    if loki_url:
        try:
            # Use a queue for async logging to avoid blocking requests
            log_queue = queue.Queue(-1)  # Unlimited queue size
            
            loki_handler = LokiHandler(
                url=loki_url,
                labels={"environment": os.getenv("ENVIRONMENT", "production")}
            )
            loki_formatter = logging.Formatter(
                '%(levelname)s - %(name)s - %(message)s'
            )
            loki_handler.setFormatter(loki_formatter)
            
            # Queue handler to avoid blocking
            queue_handler = QueueHandler(log_queue)
            root_logger.addHandler(queue_handler)
            
            # Start queue listener in background thread
            listener = QueueListener(log_queue, loki_handler, respect_handler_level=True)
            listener.start()
            
            logging.info(f"✅ Loki logging enabled: {loki_url}")
        except Exception as e:
            logging.warning(f"⚠️ Failed to setup Loki logging: {e}")
    else:
        logging.info("ℹ️  Loki logging disabled (LOKI_URL not set)")
    
    return root_logger