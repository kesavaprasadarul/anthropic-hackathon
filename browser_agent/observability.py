"""
Observability utilities for browser automation.

This module provides logging, metrics, and monitoring capabilities for
the browser automation system.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import json
import os

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('browser_automation.log') if os.path.exists('.') else logging.NullHandler()
    ]
)

# Metrics storage (in production, this would be sent to a metrics service)
_metrics_store = []


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for the given module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    
    # Redact sensitive information in logs
    class SensitiveDataFilter(logging.Filter):
        def filter(self, record):
            # Redact phone numbers and emails in log messages
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                record.msg = redact_sensitive_data(record.msg)
            return True
    
    logger.addFilter(SensitiveDataFilter())
    return logger


def redact_sensitive_data(text: str) -> str:
    """
    Redact sensitive information from text.
    
    Args:
        text: Input text that may contain sensitive data
        
    Returns:
        str: Text with sensitive data redacted
    """
    import re
    
    # Redact phone numbers
    text = re.sub(r'\+?[\d\s\-\(\)]{10,}', '[PHONE_REDACTED]', text)
    
    # Redact email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]', text)
    
    return text


def log_execution_metrics(
    task_id: str,
    business_name: str,
    intent: str,
    execution_time: float,
    steps_taken: int,
    success: bool,
    error: Optional[str] = None
) -> None:
    """
    Log execution metrics for monitoring and analysis.
    
    Args:
        task_id: Unique task identifier
        business_name: Target business name
        intent: Task intent (reserve/info)
        execution_time: Total execution time in seconds
        steps_taken: Number of browser steps executed
        success: Whether the task succeeded
        error: Error message if failed
    """
    metric = {
        'timestamp': datetime.now().isoformat(),
        'task_id': task_id,
        'business_name': business_name,
        'intent': intent,
        'execution_time_seconds': execution_time,
        'steps_taken': steps_taken,
        'success': success,
        'error': error
    }
    
    # Store metric (in production, send to metrics service)
    _metrics_store.append(metric)
    
    # Log structured metric
    logger = get_logger('metrics')
    logger.info(f"METRIC: {json.dumps(metric)}")


def log_validation_error(error_type: str, error_details: str, input_data: Dict[str, Any]) -> None:
    """
    Log input validation errors for monitoring.
    
    Args:
        error_type: Type of validation error
        error_details: Detailed error message
        input_data: Sanitized input data (sensitive info removed)
    """
    # Remove sensitive data before logging
    sanitized_data = sanitize_input_data(input_data)
    
    metric = {
        'timestamp': datetime.now().isoformat(),
        'type': 'validation_error',
        'error_type': error_type,
        'error_details': error_details,
        'input_data': sanitized_data
    }
    
    logger = get_logger('validation')
    logger.warning(f"VALIDATION_ERROR: {json.dumps(metric)}")


def sanitize_input_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive information from input data for logging.
    
    Args:
        data: Input data dictionary
        
    Returns:
        Dict: Sanitized data with sensitive fields removed
    """
    sanitized = data.copy()
    
    # Remove sensitive user information
    if 'user' in sanitized:
        user = sanitized['user'].copy()
        if 'email' in user:
            user['email'] = '[EMAIL_REDACTED]'
        if 'phone' in user:
            user['phone'] = '[PHONE_REDACTED]'
        sanitized['user'] = user
    
    # Remove sensitive business information
    if 'business' in sanitized:
        business = sanitized['business'].copy()
        if 'phone' in business:
            business['phone'] = '[PHONE_REDACTED]'
        sanitized['business'] = business
    
    return sanitized


def get_metrics_summary() -> Dict[str, Any]:
    """
    Get a summary of collected metrics.
    
    Returns:
        Dict: Metrics summary
    """
    if not _metrics_store:
        return {'total_tasks': 0}
    
    total_tasks = len(_metrics_store)
    successful_tasks = sum(1 for m in _metrics_store if m.get('success', False))
    failed_tasks = total_tasks - successful_tasks
    
    avg_execution_time = sum(m.get('execution_time_seconds', 0) for m in _metrics_store) / total_tasks
    avg_steps = sum(m.get('steps_taken', 0) for m in _metrics_store) / total_tasks
    
    # Count by intent
    intent_counts = {}
    for metric in _metrics_store:
        intent = metric.get('intent', 'unknown')
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    # Count by error type
    error_counts = {}
    for metric in _metrics_store:
        if not metric.get('success') and metric.get('error'):
            error_type = 'timeout' if 'timeout' in metric['error'].lower() else 'other'
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
    
    return {
        'total_tasks': total_tasks,
        'successful_tasks': successful_tasks,
        'failed_tasks': failed_tasks,
        'success_rate': successful_tasks / total_tasks if total_tasks > 0 else 0,
        'avg_execution_time_seconds': avg_execution_time,
        'avg_steps_per_task': avg_steps,
        'intent_distribution': intent_counts,
        'error_distribution': error_counts,
        'last_updated': datetime.now().isoformat()
    }


def reset_metrics() -> None:
    """Reset metrics store (useful for testing)."""
    global _metrics_store
    _metrics_store = []


class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        self.operation_name = operation_name
        self.logger = logger or get_logger(__name__)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Starting {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.logger.debug(f"Completed {self.operation_name} in {duration:.2f}s")
            
            if exc_type:
                self.logger.error(f"Error in {self.operation_name}: {exc_val}")


# Health check utilities
def get_health_status() -> Dict[str, Any]:
    """
    Get system health status.
    
    Returns:
        Dict: Health status information
    """
    try:
        # Basic health checks
        import psutil
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent()
        disk_usage = psutil.disk_usage('/').percent
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'memory_usage_percent': memory_usage,
            'cpu_usage_percent': cpu_usage,
            'disk_usage_percent': disk_usage,
            'recent_tasks': len([m for m in _metrics_store if (datetime.now() - datetime.fromisoformat(m['timestamp'])).total_seconds() < 3600])
        }
        
        # Check for high resource usage
        if memory_usage > 90 or cpu_usage > 90 or disk_usage > 90:
            health_status['status'] = 'warning'
            health_status['warnings'] = []
            
            if memory_usage > 90:
                health_status['warnings'].append('High memory usage')
            if cpu_usage > 90:
                health_status['warnings'].append('High CPU usage')
            if disk_usage > 90:
                health_status['warnings'].append('High disk usage')
        
        return health_status
        
    except ImportError:
        # psutil not available, return basic health
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'message': 'Basic health check (psutil not available)'
        }
    except Exception as e:
        return {
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }