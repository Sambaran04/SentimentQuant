import logging
import logging.handlers
import json
from datetime import datetime
from typing import Any, Dict
from pathlib import Path
from app.core.config import settings

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)
            
        return json.dumps(log_data)

class RequestResponseFormatter(logging.Formatter):
    """Formatter for request/response logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format request/response log record"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(record, "request_id", "unknown"),
            "method": getattr(record, "method", "unknown"),
            "path": getattr(record, "path", "unknown"),
            "status_code": getattr(record, "status_code", "unknown"),
            "duration_ms": getattr(record, "duration_ms", 0),
            "client_ip": getattr(record, "client_ip", "unknown"),
            "user_id": getattr(record, "user_id", "unknown"),
        }
        
        if hasattr(record, "request_body"):
            log_data["request_body"] = record.request_body
        if hasattr(record, "response_body"):
            log_data["response_body"] = record.response_body
            
        return json.dumps(log_data)

def setup_logging():
    """Configure logging with different handlers"""
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    json_formatter = JSONFormatter()
    request_formatter = RequestResponseFormatter()
    
    # Create handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    console_handler.setLevel(logging.INFO)
    handlers.append(console_handler)
    
    # File handler for general logs
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(logging.INFO)
    handlers.append(file_handler)
    
    # File handler for request/response logs
    request_handler = logging.handlers.RotatingFileHandler(
        log_dir / "requests.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    request_handler.setFormatter(request_formatter)
    request_handler.setLevel(logging.INFO)
    handlers.append(request_handler)
    
    # File handler for error logs
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    error_handler.setFormatter(json_formatter)
    error_handler.setLevel(logging.ERROR)
    handlers.append(error_handler)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []  # Remove existing handlers
    root_logger.addHandler(console_handler)
    
    # Configure application logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    app_logger.handlers = []  # Remove existing handlers
    for handler in handlers:
        app_logger.addHandler(handler)
    
    # Configure request logger
    request_logger = logging.getLogger("app.requests")
    request_logger.setLevel(logging.INFO)
    request_logger.handlers = []  # Remove existing handlers
    request_logger.addHandler(request_handler)
    
    return app_logger

# Create logger instance
logger = setup_logging() 