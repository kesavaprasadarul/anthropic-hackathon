"""
Public API router for browser automation.

This module provides the main API interface for browser automation tasks,
handling request routing, coordination between components, and response formatting.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from contracts import BrowserTask, BrowserAutomationResult, NextAction, Status
from input_adapter import InputAdapter, InputValidationError, create_error_result
from browser_executor import BrowserExecutor, MockBrowserExecutor
from result_processor import ResultProcessor
from observability import get_logger, log_validation_error, PerformanceTimer

logger = get_logger(__name__)


class BrowserAutomationRouter:
    """Main router for browser automation requests."""
    
    def __init__(self, use_mock_executor: bool = False):
        """
        Initialize the browser automation router.
        
        Args:
            use_mock_executor: Whether to use mock executor for testing
        """
        self.input_adapter = InputAdapter()
        self.executor = MockBrowserExecutor() if use_mock_executor else BrowserExecutor()
        self.result_processor = ResultProcessor()
        
        logger.info(f"Initialized BrowserAutomationRouter (mock: {use_mock_executor})")
    
    async def execute_automation(self, task_data: Dict[str, Any]) -> BrowserAutomationResult:
        """
        Execute a browser automation task.
        
        This is the main entry point for browser automation requests.
        
        Args:
            task_data: Raw task data from API request
            
        Returns:
            BrowserAutomationResult: Standardized automation result
        """
        task_id = task_data.get("idempotency_key") or str(uuid.uuid4())
        
        try:
            with PerformanceTimer("input_validation"):
                # Step 1: Validate and normalize input
                task = self.input_adapter.validate_task(task_data)
                
            with PerformanceTimer("browser_execution"):
                # Step 2: Execute browser automation
                final_result = await self.executor.execute(task)
                
                # Handle different result types
                if not isinstance(final_result, BrowserAutomationResult):
                    logger.error(f"Unexpected result type from executor: {type(final_result)}")
                    return BrowserAutomationResult(
                        status=Status.ERROR,
                        message="Invalid result format from browser executor",
                        next_action=NextAction.RETRY_LATER,
                        evidence=self._create_empty_evidence(),
                        error_reason="Invalid executor response"
                    )
                
            logger.info(f"Completed browser automation for task {task_id}: {final_result.status}")
            return final_result
                
        except InputValidationError as e:
            log_validation_error(task_id, task_data.get("business", {}).get("name", "unknown"), str(e))
            return create_error_result(str(e), Status.NEEDS_USER_INPUT)
            
        except Exception as e:
            logger.error(f"Unexpected error in browser automation {task_id}: {str(e)}")
            return BrowserAutomationResult(
                status=Status.ERROR,
                message=f"Unexpected system error: {str(e)}",
                next_action=NextAction.RETRY_LATER,
                evidence=self._create_empty_evidence(),
                error_reason=str(e)
            )
    
    async def execute_reservation(self, reservation_data: Dict[str, Any]) -> BrowserAutomationResult:
        """
        Execute a restaurant reservation task.
        
        Convenience method for reservation-specific requests.
        
        Args:
            reservation_data: Reservation task data
            
        Returns:
            BrowserAutomationResult: Reservation result
        """
        # Ensure intent is set to reserve
        reservation_data["intent"] = "reserve"
        
        return await self.execute_automation(reservation_data)
    
    async def execute_info_request(self, info_data: Dict[str, Any]) -> BrowserAutomationResult:
        """
        Execute an information request task.
        
        Convenience method for information request tasks.
        
        Args:
            info_data: Information request task data
            
        Returns:
            BrowserAutomationResult: Information result
        """
        # Ensure intent is set to info
        info_data["intent"] = "info"
        
        return await self.execute_automation(info_data)
    
    def _create_empty_evidence(self):
        """Create empty evidence for error cases."""
        from contracts import Evidence
        return Evidence(
            screenshots=[],
            browsing_summary="No browser automation executed due to error",
            steps_taken=0,
            duration_seconds=0.0
        )


# Global router instance (singleton pattern)
_router_instance: Optional[BrowserAutomationRouter] = None


def get_router(use_mock_executor: bool = False) -> BrowserAutomationRouter:
    """
    Get the global router instance.
    
    Args:
        use_mock_executor: Whether to use mock executor for testing
        
    Returns:
        BrowserAutomationRouter: Router instance
    """
    global _router_instance
    
    if _router_instance is None:
        _router_instance = BrowserAutomationRouter(use_mock_executor)
    
    return _router_instance


def reset_router() -> None:
    """Reset the global router instance (useful for testing)."""
    global _router_instance
    _router_instance = None


# Convenience functions for direct usage
async def execute_browser_automation(task_data: Dict[str, Any]) -> BrowserAutomationResult:
    """
    Execute browser automation with default router.
    
    Args:
        task_data: Raw task data
        
    Returns:
        BrowserAutomationResult: Automation result
    """
    router = get_router()
    return await router.execute_automation(task_data)


async def make_reservation(
    business_name: str,
    business_website: str,
    customer_name: str,
    customer_email: str,
    reservation_date: str,
    start_time: str,
    end_time: str,
    party_size: int,
    **kwargs
) -> BrowserAutomationResult:
    """
    Simplified reservation interface.
    
    Args:
        business_name: Restaurant name
        business_website: Restaurant website URL
        customer_name: Customer name
        customer_email: Customer email
        reservation_date: Date in YYYY-MM-DD format
        start_time: Start time in HH:MM format
        end_time: End time in HH:MM format
        party_size: Number of people
        **kwargs: Additional reservation parameters
        
    Returns:
        BrowserAutomationResult: Reservation result
    """
    task_data = {
        "business": {
            "name": business_name,
            "website": business_website
        },
        "user": {
            "name": customer_name,
            "email": customer_email
        },
        "intent": "reserve",
        "reservation": {
            "date": reservation_date,
            "time_window": {
                "start_time": start_time,
                "end_time": end_time
            },
            "party_size": party_size,
            **kwargs
        }
    }
    
    router = get_router()
    return await router.execute_automation(task_data)


async def get_business_info(
    business_name: str,
    business_website: str,
    info_type: str,
    **kwargs
) -> BrowserAutomationResult:
    """
    Simplified business information interface.
    
    Args:
        business_name: Business name
        business_website: Business website URL
        info_type: Type of information to request
        **kwargs: Additional context parameters
        
    Returns:
        BrowserAutomationResult: Information result
    """
    task_data = {
        "business": {
            "name": business_name,
            "website": business_website
        },
        "user": {
            "name": "Information Requester",
            "email": "info@example.com"
        },
        "intent": "info",
        "info": {
            "info_type": info_type,
            **kwargs
        }
    }
    
    router = get_router()
    return await router.execute_automation(task_data)