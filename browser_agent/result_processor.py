"""
Result processing and normalization for browser automation.

This module handles the processing of raw browser automation results into
standardized BrowserAutomationResult objects with proper status mapping
and artifact extraction.
"""

import json
import re
from typing import Any, Dict, Optional, Union
from datetime import datetime, date, time

from contracts import (
    BrowserTask, BrowserAutomationResult, BookingDetails, InfoResponse,
    Evidence, Status, NextAction, Intent, InfoType
)
from observability import get_logger

logger = get_logger(__name__)


class ResultProcessor:
    """Processes and normalizes browser automation results."""
    
    def process_result(self, raw_result: Any, task: BrowserTask, evidence: Evidence) -> BrowserAutomationResult:
        """
        Process raw browser automation results into standardized format.
        
        Args:
            raw_result: Raw result from browser agent
            task: Original browser automation task
            evidence: Collected execution evidence
            
        Returns:
            BrowserAutomationResult: Standardized result
        """
        try:
            if task.intent == Intent.RESERVE:
                return self._process_reservation_result(raw_result, task, evidence)
            elif task.intent == Intent.INFO:
                return self._process_info_result(raw_result, task, evidence)
            else:
                return self._create_error_result(
                    f"Unsupported intent: {task.intent}",
                    evidence,
                    Status.ERROR
                )
        
        except Exception as e:
            logger.error(f"Error processing result for task {task.idempotency_key}: {str(e)}")
            return self._create_error_result(
                f"Result processing failed: {str(e)}",
                evidence,
                Status.ERROR
            )
    
    def _process_reservation_result(
        self, 
        raw_result: Any, 
        task: BrowserTask, 
        evidence: Evidence
    ) -> BrowserAutomationResult:
        """Process reservation automation results."""
        
        # Parse raw result
        parsed_result = self._parse_raw_result(raw_result)
        
        if not parsed_result:
            return self._create_error_result(
                "No result returned from browser automation",
                evidence,
                Status.ERROR
            )
        
        # Check if reservation was successful
        success = parsed_result.get("success", False)
        
        if success:
            return self._create_successful_reservation_result(parsed_result, task, evidence)
        else:
            return self._create_failed_reservation_result(parsed_result, task, evidence)
    
    def _create_successful_reservation_result(
        self, 
        result: Dict[str, Any], 
        task: BrowserTask, 
        evidence: Evidence
    ) -> BrowserAutomationResult:
        """Create successful reservation result."""
        
        # Extract booking details
        booking_details = self._extract_booking_details(result, task)
        
        # Determine next action
        next_action = NextAction.ADD_TO_CALENDAR
        
        # Create success message
        message = "Successfully completed reservation"
        if booking_details.booking_reference:
            message += f". Booking reference: {booking_details.booking_reference}"
        
        return BrowserAutomationResult(
            status=Status.COMPLETED,
            message=message,
            next_action=next_action,
            core_artifact=booking_details,
            evidence=evidence
        )
    
    def _create_failed_reservation_result(
        self, 
        result: Dict[str, Any], 
        task: BrowserTask, 
        evidence: Evidence
    ) -> BrowserAutomationResult:
        """Create failed reservation result."""
        
        # Determine failure reason and status
        error_type = result.get("error_type", "").upper()
        error_details = result.get("error_details", "Unknown error")
        
        # Map error types to statuses and next actions
        status_mapping = {
            "NO_WEBSITE": (Status.NO_WEBSITE, NextAction.SWITCH_CHANNEL),
            "RESTAURANT_CLOSED": (Status.RESTAURANT_CLOSED, NextAction.RETRY_LATER),
            "NO_AVAILABILITY": (Status.NO_AVAILABILITY, NextAction.REQUEST_USER_INPUT),
            "TIMEOUT": (Status.TIMEOUT, NextAction.RETRY_LATER),
            "MISSING_INFORMATION": (Status.NEEDS_USER_INPUT, NextAction.REQUEST_USER_INPUT),
        }
        
        status, next_action = status_mapping.get(error_type, (Status.ERROR, NextAction.SWITCH_CHANNEL))
        
        # Create appropriate message
        message_mapping = {
            Status.NO_WEBSITE: "Could not access restaurant website or no online reservations available",
            Status.RESTAURANT_CLOSED: "Restaurant is closed during the requested time",
            Status.NO_AVAILABILITY: "No availability found for the requested date/time",
            Status.TIMEOUT: "Reservation process timed out",
            Status.NEEDS_USER_INPUT: "Additional information required to complete reservation",
            Status.ERROR: "An error occurred during the reservation process"
        }
        
        message = message_mapping.get(status, error_details)
        
        return BrowserAutomationResult(
            status=status,
            message=message,
            next_action=next_action,
            evidence=evidence,
            error_reason=error_details
        )
    
    def _extract_booking_details(self, result: Dict[str, Any], task: BrowserTask) -> BookingDetails:
        """Extract booking details from successful reservation result."""
        
        payload = task.payload  # ReservePayload
        
        # Extract confirmed details (fallback to requested if not provided)
        confirmed_date_str = result.get("confirmed_date")
        confirmed_time_str = result.get("confirmed_time")
        
        try:
            confirmed_date = datetime.fromisoformat(confirmed_date_str).date() if confirmed_date_str else payload.date
        except (ValueError, AttributeError):
            confirmed_date = payload.date
        
        try:
            confirmed_time = datetime.fromisoformat(confirmed_time_str).time() if confirmed_time_str else payload.time_window_start
        except (ValueError, AttributeError):
            confirmed_time = payload.time_window_start
        
        # Extract confirmation reference
        confirmation_details = result.get("confirmation_details", "")
        booking_reference = self._extract_reference_number(confirmation_details)
        
        return BookingDetails(
            booking_reference=booking_reference,
            confirmed_date=confirmed_date,
            confirmed_time=confirmed_time,
            party_size=result.get("party_size", payload.party_size),
            customer_name=task.user.name,
            restaurant_name=task.business.name,
            special_requests=payload.notes
        )
    
    def _extract_reference_number(self, confirmation_text: str) -> Optional[str]:
        """Extract booking reference number from confirmation text."""
        if not confirmation_text:
            return None
        
        # Common patterns for confirmation numbers
        patterns = [
            r"confirmation\s*(?:number|#|code)?\s*:?\s*([A-Z0-9]+)",
            r"reference\s*(?:number|#|code)?\s*:?\s*([A-Z0-9]+)",
            r"booking\s*(?:number|#|code)?\s*:?\s*([A-Z0-9]+)",
            r"reservation\s*(?:number|#|code)?\s*:?\s*([A-Z0-9]+)",
            r"#([A-Z0-9]{4,})",
            r"([A-Z]{2,}\d{4,})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, confirmation_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _process_info_result(
        self, 
        raw_result: Any, 
        task: BrowserTask, 
        evidence: Evidence
    ) -> BrowserAutomationResult:
        """Process information request results."""
        
        parsed_result = self._parse_raw_result(raw_result)
        
        if not parsed_result:
            return self._create_error_result(
                "No result returned from browser automation",
                evidence,
                Status.ERROR
            )
        
        # Check if information was found
        info_found = parsed_result.get("info_found", False)
        
        if info_found:
            return self._create_successful_info_result(parsed_result, task, evidence)
        else:
            return self._create_failed_info_result(parsed_result, task, evidence)
    
    def _create_successful_info_result(
        self, 
        result: Dict[str, Any], 
        task: BrowserTask, 
        evidence: Evidence
    ) -> BrowserAutomationResult:
        """Create successful information result."""
        
        payload = task.payload  # InfoPayload
        
        # Extract information response
        info_data = result.get("data", "")
        additional_context = result.get("additional_context", "")
        source_section = result.get("source_section", "")
        limitations = result.get("limitations", "")
        
        # Combine additional notes
        notes_parts = []
        if source_section:
            notes_parts.append(f"Source: {source_section}")
        if additional_context:
            notes_parts.append(f"Context: {additional_context}")
        if limitations:
            notes_parts.append(f"Limitations: {limitations}")
        
        additional_notes = " | ".join(notes_parts) if notes_parts else None
        
        info_response = InfoResponse(
            info_type=payload.info_type,
            data=info_data,
            additional_notes=additional_notes,
            source_url=task.business.website
        )
        
        message = f"Successfully retrieved {payload.info_type.value} information"
        
        return BrowserAutomationResult(
            status=Status.COMPLETED,
            message=message,
            next_action=NextAction.NONE,
            core_artifact=info_response,
            evidence=evidence
        )
    
    def _create_failed_info_result(
        self, 
        result: Dict[str, Any], 
        task: BrowserTask, 
        evidence: Evidence
    ) -> BrowserAutomationResult:
        """Create failed information result."""
        
        payload = task.payload  # InfoPayload
        
        # Determine why information wasn't found
        limitations = result.get("limitations", "")
        error_reason = limitations or "Requested information not found on website"
        
        message = f"Could not find {payload.info_type.value} information"
        
        return BrowserAutomationResult(
            status=Status.NO_WEBSITE,  # Information not available on website
            message=message,
            next_action=NextAction.SWITCH_CHANNEL,
            evidence=evidence,
            error_reason=error_reason
        )
    
    def _parse_raw_result(self, raw_result: Any) -> Optional[Dict[str, Any]]:
        """Parse raw result into dictionary format."""
        if not raw_result:
            return None
        
        # If it's already a dict, return it
        if isinstance(raw_result, dict):
            return raw_result
        
        # Try to parse as JSON string
        if isinstance(raw_result, str):
            try:
                return json.loads(raw_result)
            except json.JSONDecodeError:
                # Try to extract JSON from text
                json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                
                # Return as plain text result
                return {"success": False, "error_details": raw_result}
        
        # Convert other types to string representation
        return {"success": False, "error_details": str(raw_result)}
    
    def _create_error_result(
        self, 
        error_message: str, 
        evidence: Evidence, 
        status: Status = Status.ERROR
    ) -> BrowserAutomationResult:
        """Create a standardized error result."""
        
        next_action_mapping = {
            Status.ERROR: NextAction.RETRY_LATER,
            Status.TIMEOUT: NextAction.RETRY_LATER,
            Status.NO_WEBSITE: NextAction.SWITCH_CHANNEL,
            Status.NEEDS_USER_INPUT: NextAction.REQUEST_USER_INPUT
        }
        
        next_action = next_action_mapping.get(status, NextAction.NONE)
        
        return BrowserAutomationResult(
            status=status,
            message=f"Browser automation failed: {error_message}",
            next_action=next_action,
            evidence=evidence,
            error_reason=error_message
        )