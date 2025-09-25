"""
Input validation and normalization for browser automation requests.

This module handles validation, normalization, and transformation of incoming
request data into standardized BrowserTask objects.
"""

from datetime import date, time, datetime
from typing import Dict, Any, Optional, Union
from pydantic import ValidationError
import logging

from contracts import (
    BrowserTask, TargetBusiness, User, Intent, InfoType, NextAction,
    ReservePayload, InfoPayload, Policy, Status, BrowserAutomationResult,
    Evidence
)

logger = logging.getLogger(__name__)


class InputValidationError(Exception):
    """Raised when input validation fails."""
    pass


class InputAdapter:
    """Handles input validation and normalization for browser automation."""
    
    def validate_task(self, task_data: Dict[str, Any]) -> BrowserTask:
        """
        Validate and normalize input task data into a BrowserTask.
        
        Args:
            task_data: Raw input data dictionary
            
        Returns:
            BrowserTask: Validated and normalized task
            
        Raises:
            InputValidationError: If validation fails
        """
        try:
            # Validate business information
            business_data = task_data.get("business", {})
            if not business_data:
                raise InputValidationError("Business information is required")
            
            business = self._validate_business(business_data)
            
            # Validate user information  
            user_data = task_data.get("user", {})
            if not user_data:
                raise InputValidationError("User information is required")
            
            user = self._validate_user(user_data)
            
            # Validate intent
            intent_str = task_data.get("intent", "").lower()
            if intent_str not in [Intent.RESERVE, Intent.INFO]:
                raise InputValidationError(f"Invalid intent: {intent_str}. Must be 'reserve' or 'info'")
            
            intent = Intent(intent_str)
            
            # Validate payload based on intent
            payload = self._validate_payload(task_data, intent)
            
            # Validate policy (optional)
            policy_data = task_data.get("policy", {})
            policy = self._validate_policy(policy_data)
            
            # Get locale (optional)
            locale = task_data.get("locale", "en-US")
            
            # Get idempotency key (optional)
            idempotency_key = task_data.get("idempotency_key")
            
            # Create the validated task
            task = BrowserTask(
                business=business,
                user=user,
                intent=intent,
                payload=payload,
                policy=policy,
                locale=locale,
                idempotency_key=idempotency_key
            )
            
            # Perform additional cross-field validation
            self._cross_validate(task)
            
            logger.info(f"Successfully validated browser task for {business.name}, intent: {intent}")
            return task
            
        except ValidationError as e:
            error_msg = f"Input validation error: {str(e)}"
            logger.error(error_msg)
            raise InputValidationError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected validation error: {str(e)}"
            logger.error(error_msg)
            raise InputValidationError(error_msg)
    
    def _validate_business(self, business_data: Dict[str, Any]) -> TargetBusiness:
        """Validate business information."""
        name = business_data.get("name", "").strip()
        if not name:
            raise InputValidationError("Business name is required")
        
        website = business_data.get("website", "").strip()        
        phone = business_data.get("phone")
        timezone = business_data.get("timezone")
        
        return TargetBusiness(
            name=name,
            website=website,
            phone=phone,
            timezone=timezone
        )
    
    def _validate_user(self, user_data: Dict[str, Any]) -> User:
        """Validate user information."""
        name = user_data.get("name", "").strip()
        if not name:
            raise InputValidationError("User name is required")
        
        email = user_data.get("email")
        phone = user_data.get("phone")
        
        # At least one contact method should be provided
        if not email and not phone:
            raise InputValidationError("User email or phone is required")
        
        return User(
            name=name,
            email=email,
            phone=phone
        )
    
    def _validate_payload(self, task_data: Dict[str, Any], intent: Intent) -> Union[ReservePayload, InfoPayload]:
        """Validate payload based on intent type."""
        if intent == Intent.RESERVE:
            return self._validate_reservation_payload(task_data)
        elif intent == Intent.INFO:
            return self._validate_info_payload(task_data)
        else:
            raise InputValidationError(f"Unsupported intent: {intent}")
    
    def _validate_reservation_payload(self, task_data: Dict[str, Any]) -> ReservePayload:
        """Validate reservation payload."""
        reservation_data = task_data.get("reservation", {})
        if not reservation_data:
            raise InputValidationError("Reservation details are required for reserve intent")
        
        # Parse date
        date_str = reservation_data.get("date")
        if not date_str:
            raise InputValidationError("Reservation date is required")
        
        try:
            reservation_date = datetime.fromisoformat(date_str).date() if isinstance(date_str, str) else date_str
        except (ValueError, TypeError):
            raise InputValidationError(f"Invalid date format: {date_str}")
        
        # Parse time window
        time_window = reservation_data.get("time_window", {})
        if not time_window:
            raise InputValidationError("Time window is required")
        
        try:
            start_time_str = time_window.get("start_time")
            end_time_str = time_window.get("end_time")
            
            if not start_time_str or not end_time_str:
                raise InputValidationError("Both start_time and end_time are required")
            
            start_time = datetime.strptime(start_time_str, "%H:%M").time() if isinstance(start_time_str, str) else start_time_str
            end_time = datetime.strptime(end_time_str, "%H:%M").time() if isinstance(end_time_str, str) else end_time_str
        except (ValueError, TypeError):
            raise InputValidationError("Invalid time format in time window")
        
        # Validate party size
        party_size = reservation_data.get("party_size")
        if not party_size or party_size < 1:
            raise InputValidationError("Valid party size is required (minimum 1)")
        
        # Optional fields
        duration_minutes = reservation_data.get("duration_minutes")
        notes = reservation_data.get("notes", "").strip() or None
        preferences = reservation_data.get("preferences", "").strip() or None
        budget = reservation_data.get("budget")
        
        return ReservePayload(
            date=reservation_date,
            time_window_start=start_time,
            time_window_end=end_time,
            party_size=party_size,
            duration_minutes=duration_minutes,
            notes=notes,
            preferences=preferences,
            budget=budget
        )
    
    def _validate_info_payload(self, task_data: Dict[str, Any]) -> InfoPayload:
        """Validate information request payload."""
        info_data = task_data.get("info", {})
        if not info_data:
            raise InputValidationError("Info details are required for info intent")
        
        # Validate info type
        info_type_str = info_data.get("info_type", "").lower()
        if info_type_str not in [e.value for e in InfoType]:
            raise InputValidationError(f"Invalid info_type: {info_type_str}")
        
        info_type = InfoType(info_type_str)
        
        # Optional context fields
        context_date = None
        context_time = None
        
        if info_data.get("context_date"):
            try:
                context_date = datetime.fromisoformat(info_data["context_date"]).date()
            except (ValueError, TypeError):
                raise InputValidationError("Invalid context_date format")
        
        if info_data.get("context_time"):
            try:
                context_time = datetime.strptime(info_data["context_time"], "%H:%M").time()
            except (ValueError, TypeError):
                raise InputValidationError("Invalid context_time format")
        
        return InfoPayload(
            info_type=info_type,
            context_date=context_date,
            context_time=context_time
        )
    
    def _validate_policy(self, policy_data: Dict[str, Any]) -> Policy:
        """Validate automation policy."""
        autonomy_level = policy_data.get("autonomy_level", "medium")
        if autonomy_level not in ["low", "medium", "high"]:
            raise InputValidationError(f"Invalid autonomy_level: {autonomy_level}")
        
        max_steps = policy_data.get("max_steps", 30)
        if max_steps < 1 or max_steps > 100:
            raise InputValidationError("max_steps must be between 1 and 100")
        
        take_screenshots = policy_data.get("take_screenshots", True)
        use_vision = policy_data.get("use_vision", True)
        max_failures = policy_data.get("max_failures", 3)
        
        if max_failures < 1 or max_failures > 10:
            raise InputValidationError("max_failures must be between 1 and 10")
        
        return Policy(
            autonomy_level=autonomy_level,
            max_steps=max_steps,
            take_screenshots=take_screenshots,
            use_vision=use_vision,
            max_failures=max_failures
        )
    
    def _cross_validate(self, task: BrowserTask) -> None:
        """Perform cross-field validation."""
        # Validate reservation date is not in the past
        if task.intent == Intent.RESERVE:
            reservation_payload = task.payload
            if reservation_payload.date < date.today():
                raise InputValidationError("Reservation date cannot be in the past")
            
            # Validate time window makes sense
            if reservation_payload.time_window_start >= reservation_payload.time_window_end:
                raise InputValidationError("Start time must be before end time")
        
        logger.debug(f"Cross-validation passed for task {task.idempotency_key}")


def create_error_result(error_message: str, next_action: NextAction = NextAction.REQUEST_USER_INPUT) -> BrowserAutomationResult:
    """Create a standardized error result for input validation failures."""
    return BrowserAutomationResult(
        status=Status.NEEDS_USER_INPUT,
        message=f"Input validation failed: {error_message}",
        next_action=next_action,
        evidence=Evidence(
            screenshots=[],
            browsing_summary="Input validation failed before browser automation started",
            steps_taken=0
        ),
        error_reason=error_message
    )