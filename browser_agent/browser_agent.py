"""
Browser Automation Module

A modular browser automation system for restaurant reservations and information requests.
This module provides a clean, scalable architecture for browser-based task automation.

## Features

- **Modular Architecture**: Clean separation of concerns across multiple modules
- **Input Validation**: Comprehensive validation and normalization of task inputs
- **Browser Automation**: Uses browser-use agent for robust web interaction
- **Result Processing**: Standardized result processing and status mapping
- **Observability**: Structured logging, metrics collection, and monitoring
- **Error Handling**: Proper error handling with detailed status reporting

## Quick Start

```python
from browser_agent import make_reservation, get_business_info

# Make a reservation
result = await make_reservation(
    business_name="Restaurant Name",
    business_website="https://restaurant.com",
    customer_name="John Doe",
    customer_email="john@email.com",
    reservation_date="2025-09-30",
    start_time="19:00",
    end_time="20:00",
    party_size=4
)

# Get business information
info_result = await get_business_info(
    business_name="Restaurant Name", 
    business_website="https://restaurant.com",
    info_type="opening_hours"
)
```

## Architecture

The module uses a modular architecture with the following components:

- `contracts.py` - Data structures and interfaces
- `input_adapter.py` - Input validation and normalization  
- `payload_builder.py` - Task instruction building
- `browser_executor.py` - Browser automation execution
- `result_processor.py` - Result processing and normalization
- `router.py` - Public API interface
- `observability.py` - Logging and metrics

## Status Vocabulary

Standardized status responses:
- `completed` - Task succeeded
- `no_availability` - No slots available  
- `no_website` - Website inaccessible
- `restaurant_closed` - Business closed during requested time
- `needs_user_input` - Missing required information
- `timeout` - Process exceeded time limits
- `error` - Technical failure

## Next Actions

Suggested follow-up actions:
- `add_to_calendar` - Add confirmed booking to calendar
- `retry_later` - Retry at a different time
- `request_user_input` - Ask user for additional information  
- `switch_channel` - Try different communication method
- `none` - No specific action needed
"""

# Re-export main interfaces for backward compatibility and convenience
from router import (
    execute_browser_automation,
    make_reservation, 
    get_business_info,
    get_router,
    BrowserAutomationRouter
)

from contracts import (
    BrowserTask,
    BrowserAutomationResult, 
    TargetBusiness,
    User,
    ReservePayload,
    InfoPayload,
    BookingDetails,
    InfoResponse,
    Intent,
    Status,
    NextAction,
    InfoType,
    Evidence
)

from observability import get_metrics_summary, get_health_status

# Legacy compatibility imports
from contracts import Intent as IntentEnum  # For backward compatibility
BrowserAgent = BrowserAutomationRouter  # Legacy class name alias


# Version information
__version__ = "2.0.0"
__author__ = "Browser Automation Team"


# Convenience functions for common use cases
async def process_browser_request(task_data):
    """
    Legacy function for backward compatibility.
    
    Args:
        task_data: Browser automation task data
        
    Returns:
        BrowserAutomationResult: Automation result
    """
    return await execute_browser_automation(task_data)


# Health check and metrics endpoints
def health_check():
    """Get system health status."""
    return get_health_status()


def metrics():
    """Get system metrics summary.""" 
    return get_metrics_summary()

