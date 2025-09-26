"""
Result processor for browser automation tasks.
"""

from typing import Dict, Any, Optional, Union, List
import re
import json
import logging
from datetime import datetime, date, time

from contracts import (
    BrowserTask, BrowserAutomationResult, BookingDetails, InfoResponse, RecommendResponse,
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
            elif task.intent == Intent.RECOMMEND:
                return self._process_recommend_result(raw_result, task, evidence)
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
        
        # Create model rationale from the result
        model_rationale = result.get("confirmation_details", "Successfully completed reservation")
        if booking_details.booking_reference:
            model_rationale += f". Booking reference: {booking_details.booking_reference}"
        
        return BrowserAutomationResult(
            status=Status.COMPLETED,
            artifact=booking_details,
            model_rationale=model_rationale,
            evidence=evidence,
            # Legacy fields for backward compatibility
            message=model_rationale,
            next_action=NextAction.ADD_TO_CALENDAR
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
        
        # Create appropriate model rationale
        message_mapping = {
            Status.NO_WEBSITE: "Could not access restaurant website or no online reservations available",
            Status.RESTAURANT_CLOSED: "Restaurant is closed during the requested time",
            Status.NO_AVAILABILITY: "No availability found for the requested date/time",
            Status.TIMEOUT: "Reservation process timed out",
            Status.NEEDS_USER_INPUT: "Additional information required to complete reservation",
            Status.ERROR: "An error occurred during the reservation process"
        }
        
        model_rationale = message_mapping.get(status, error_details)
        
        return BrowserAutomationResult(
            status=status,
            artifact=None,  # No booking details for failed reservation
            model_rationale=model_rationale,
            evidence=evidence,
            error_reason=error_details,
            # Legacy fields for backward compatibility
            message=model_rationale,
            next_action=next_action
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
        
        model_rationale = f"Successfully retrieved {payload.info_type.value} information: {info_data}"
        
        return BrowserAutomationResult(
            status=Status.COMPLETED,
            artifact=info_response,
            model_rationale=model_rationale,
            evidence=evidence,
            # Legacy fields for backward compatibility
            message=model_rationale,
            next_action=NextAction.NONE
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
        
        model_rationale = f"Could not find {payload.info_type.value} information. {error_reason}"
        
        return BrowserAutomationResult(
            status=Status.NO_WEBSITE,  # Information not available on website
            artifact=None,
            model_rationale=model_rationale,
            evidence=evidence,
            error_reason=error_reason,
            # Legacy fields for backward compatibility
            message=model_rationale,
            next_action=NextAction.SWITCH_CHANNEL
        )
    
    def _process_recommend_result(
        self, 
        raw_result: Any, 
        task: BrowserTask, 
        evidence: Evidence
    ) -> BrowserAutomationResult:
        """Process restaurant recommendation results."""
        
        parsed_result = self._parse_raw_result(raw_result)
        
        if not parsed_result:
            return self._create_error_result(
                "No result returned from browser automation",
                evidence,
                Status.ERROR
            )
        
        # Check if recommendations were found
        recommendations_found = parsed_result.get("recommendations_found", False)
        
        if recommendations_found:
            return self._create_successful_recommend_result(parsed_result, task, evidence)
        else:
            return self._create_failed_recommend_result(parsed_result, task, evidence)
    
    def _create_successful_recommend_result(
        self, 
        result: Dict[str, Any], 
        task: BrowserTask, 
        evidence: Evidence
    ) -> BrowserAutomationResult:
        """Create successful recommendation result."""
        
        payload = task.payload  # RecommendPayload
        
        # Extract recommendation data
        recommendations = result.get("recommendations", [])
        search_area = result.get("search_area", payload.area)
        budget_range = result.get("budget_range", f"{payload.budget}€")
        limitations = result.get("limitations", "")
        
        recommend_response = RecommendResponse(
            recommendations_found=True,
            recommendations=recommendations,
            search_area=search_area,
            budget_range=budget_range,
            additional_notes=limitations if limitations else None
        )
        
        # Create model rationale with summary of recommendations
        restaurant_names = [rec.get("name", "Unknown") for rec in recommendations[:2]]
        model_rationale = f"Found {len(recommendations)} restaurant recommendations in {search_area} within {budget_range} budget"
        if restaurant_names:
            model_rationale += f": {', '.join(restaurant_names)}"
            if len(recommendations) > 2:
                model_rationale += f" and {len(recommendations) - 2} more"
        
        return BrowserAutomationResult(
            status=Status.COMPLETED,
            artifact=recommend_response,
            model_rationale=model_rationale,
            evidence=evidence,
            # Legacy fields for backward compatibility
            message=model_rationale,
            next_action=NextAction.NONE
        )
    
    def _create_failed_recommend_result(
        self, 
        result: Dict[str, Any], 
        task: BrowserTask, 
        evidence: Evidence
    ) -> BrowserAutomationResult:
        """Create failed recommendation result."""
        
        payload = task.payload  # RecommendPayload
        
        # Determine why recommendations weren't found
        limitations = result.get("limitations", "")
        error_reason = limitations or f"Could not find suitable restaurant recommendations in {payload.area}"
        
        model_rationale = f"No restaurant recommendations found in {payload.area} within {payload.budget}€ budget. {error_reason}"
        
        return BrowserAutomationResult(
            status=Status.NO_AVAILABILITY,  # No suitable options found
            artifact=None,
            model_rationale=model_rationale,
            evidence=evidence,
            error_reason=error_reason,
            # Legacy fields for backward compatibility
            message=model_rationale,
            next_action=NextAction.REQUEST_USER_INPUT
        )
    
    def _parse_raw_result(self, raw_result: Any) -> Optional[Dict[str, Any]]:
        """Parse raw result (browser-use history) into dictionary format."""
        if not raw_result:
            return None
        
        # Check if this is a browser-use history object with the expected methods
        if hasattr(raw_result, 'is_successful') and hasattr(raw_result, 'final_result'):
            try:
                # Extract information from browser-use history API
                is_successful = raw_result.is_successful() if callable(getattr(raw_result, 'is_successful')) else raw_result.is_successful
                final_content = raw_result.final_result() if callable(getattr(raw_result, 'final_result')) else raw_result.final_result
                
                # Try to parse the final result as JSON if it's a string
                if isinstance(final_content, str):
                    try:
                        parsed_content = json.loads(final_content)
                        if isinstance(parsed_content, dict):
                            parsed_content['success'] = is_successful
                            return parsed_content
                    except json.JSONDecodeError:
                        pass
                
                # Fallback: create a simple result structure
                return {
                    'success': is_successful,
                    'data': final_content,
                    'model_output': str(final_content)
                }
                
            except Exception as e:
                logger.warning(f"Error parsing browser-use history: {str(e)}")
                return {'success': False, 'error_details': str(e)}
        
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
        model_rationale = f"Browser automation failed: {error_message}"
        
        return BrowserAutomationResult(
            status=status,
            artifact=None,
            model_rationale=model_rationale,
            evidence=evidence,
            error_reason=error_message,
            # Legacy fields for backward compatibility
            message=model_rationale,
            next_action=next_action
        )