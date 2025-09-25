"""
Input validation and normalization for call tasks.

Validates incoming task requests and normalizes them into standardized CallTask objects.
"""

from datetime import datetime, time
from typing import Optional, List
import hashlib
import re

from .contracts import (
    CallTask, CallPolicy, ValidationResult, ValidationError,
    TaskIntent, BusinessInfo, UserInfo, TimeWindow,
    ReservationTask, RescheduleTask, CancelTask, InfoTask
)


class InputAdapter:
    """Handles input validation and normalization."""
    
    def __init__(self):
        self.phone_pattern = re.compile(r'^\+[1-9]\d{1,14}$')  # E.164 format
        self.time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')  # HH:MM format
    
    def validate(self, task_data: dict) -> ValidationResult:
        """
        Validate and normalize incoming task data.
        
        Args:
            task_data: Raw task data from supervisor
            
        Returns:
            ValidationResult with normalized task or errors
        """
        errors = []
        
        # Validate envelope fields
        envelope_result = self._validate_envelope(task_data)
        if not envelope_result.is_valid:
            errors.extend(envelope_result.errors)
            return ValidationResult(is_valid=False, errors=errors)
        
        # Validate intent-specific payload
        intent = TaskIntent(task_data.get("intent"))
        payload_result = self._validate_payload(task_data, intent)
        if not payload_result.is_valid:
            errors.extend(payload_result.errors)
            return ValidationResult(is_valid=False, errors=errors)
        
        # Build normalized task
        try:
            normalized_task = self._build_normalized_task(task_data, intent)
            return ValidationResult(is_valid=True, normalized_task=normalized_task)
        except Exception as e:
            errors.append(ValidationError(
                field="general",
                message=f"Failed to normalize task: {str(e)}",
                required_for_intent=intent
            ))
            return ValidationResult(is_valid=False, errors=errors)
    
    def _validate_envelope(self, task_data: dict) -> ValidationResult:
        """Validate envelope fields (business, user, intent, etc.)."""
        errors = []
        
        # Required envelope fields
        required_fields = ["business", "user", "intent"]
        missing_fields = [field for field in required_fields if field not in task_data]
        
        if missing_fields:
            errors.append(ValidationError(
                field="envelope",
                message=f"Missing required fields: {', '.join(missing_fields)}",
                required_for_intent=TaskIntent.RESERVE  # Generic for envelope
            ))
            return ValidationResult(is_valid=False, errors=errors)
        
        # Validate business info
        business_data = task_data["business"]
        if not business_data.get("phone"):
            errors.append(ValidationError(
                field="business.phone",
                message="Business phone number is required",
                required_for_intent=TaskIntent.RESERVE
            ))
        elif not self._is_valid_phone(business_data["phone"]):
            errors.append(ValidationError(
                field="business.phone",
                message="Phone number must be in E.164 format (e.g., +1234567890)",
                required_for_intent=TaskIntent.RESERVE
            ))
        
        # Validate user info
        user_data = task_data["user"]
        if not user_data.get("name"):
            errors.append(ValidationError(
                field="user.name",
                message="User name is required",
                required_for_intent=TaskIntent.RESERVE
            ))
        
        # Validate intent
        try:
            TaskIntent(task_data["intent"])
        except ValueError:
            errors.append(ValidationError(
                field="intent",
                message=f"Invalid intent. Must be one of: {[i.value for i in TaskIntent]}",
                required_for_intent=TaskIntent.RESERVE
            ))
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    def _validate_payload(self, task_data: dict, intent: TaskIntent) -> ValidationResult:
        """Validate intent-specific payload."""
        errors = []
        
        if intent == TaskIntent.RESERVE:
            errors.extend(self._validate_reservation_payload(task_data))
        elif intent == TaskIntent.RESCHEDULE:
            errors.extend(self._validate_reschedule_payload(task_data))
        elif intent == TaskIntent.CANCEL:
            errors.extend(self._validate_cancel_payload(task_data))
        elif intent == TaskIntent.INFO:
            errors.extend(self._validate_info_payload(task_data))
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    def _validate_reservation_payload(self, task_data: dict) -> List[ValidationError]:
        """Validate reservation-specific fields."""
        errors = []
        
        if "reservation" not in task_data:
            errors.append(ValidationError(
                field="reservation",
                message="Reservation details are required for reserve intent",
                required_for_intent=TaskIntent.RESERVE
            ))
            return errors
        
        reservation = task_data["reservation"]
        
        # Validate date
        if not reservation.get("date"):
            errors.append(ValidationError(
                field="reservation.date",
                message="Reservation date is required",
                required_for_intent=TaskIntent.RESERVE
            ))
        
        # Validate time window
        if not reservation.get("time_window"):
            errors.append(ValidationError(
                field="reservation.time_window",
                message="Time window is required",
                required_for_intent=TaskIntent.RESERVE
            ))
        
        # Validate party size
        if not reservation.get("party_size") or reservation["party_size"] < 1:
            errors.append(ValidationError(
                field="reservation.party_size",
                message="Party size must be at least 1",
                required_for_intent=TaskIntent.RESERVE
            ))
        
        return errors
    
    def _validate_reschedule_payload(self, task_data: dict) -> List[ValidationError]:
        """Validate reschedule-specific fields."""
        errors = []
        
        if "reschedule" not in task_data:
            errors.append(ValidationError(
                field="reschedule",
                message="Reschedule details are required for reschedule intent",
                required_for_intent=TaskIntent.RESCHEDULE
            ))
            return errors
        
        reschedule = task_data["reschedule"]
        
        # Must have either booking reference or disambiguation bundle
        if not reschedule.get("booking_reference") and not reschedule.get("disambiguation_bundle"):
            errors.append(ValidationError(
                field="reschedule.identification",
                message="Either booking_reference or disambiguation_bundle is required",
                required_for_intent=TaskIntent.RESCHEDULE
            ))
        
        # Validate new date/time
        if not reschedule.get("new_date"):
            errors.append(ValidationError(
                field="reschedule.new_date",
                message="New date is required for reschedule",
                required_for_intent=TaskIntent.RESCHEDULE
            ))
        
        if not reschedule.get("new_time_window"):
            errors.append(ValidationError(
                field="reschedule.new_time_window",
                message="New time window is required for reschedule",
                required_for_intent=TaskIntent.RESCHEDULE
            ))
        
        return errors
    
    def _validate_cancel_payload(self, task_data: dict) -> List[ValidationError]:
        """Validate cancellation-specific fields."""
        errors = []
        
        if "cancel" not in task_data:
            errors.append(ValidationError(
                field="cancel",
                message="Cancel details are required for cancel intent",
                required_for_intent=TaskIntent.CANCEL
            ))
            return errors
        
        cancel = task_data["cancel"]
        
        # Must have either booking reference or disambiguation bundle
        if not cancel.get("booking_reference") and not cancel.get("disambiguation_bundle"):
            errors.append(ValidationError(
                field="cancel.identification",
                message="Either booking_reference or disambiguation_bundle is required",
                required_for_intent=TaskIntent.CANCEL
            ))
        
        return errors
    
    def _validate_info_payload(self, task_data: dict) -> List[ValidationError]:
        """Validate info request-specific fields."""
        errors = []
        
        if "info" not in task_data:
            errors.append(ValidationError(
                field="info",
                message="Info details are required for info intent",
                required_for_intent=TaskIntent.INFO
            ))
            return errors
        
        info = task_data["info"]
        
        # Validate question type
        valid_question_types = ["availability", "status", "hours", "price", "policies"]
        if not info.get("question_type") or info["question_type"] not in valid_question_types:
            errors.append(ValidationError(
                field="info.question_type",
                message=f"Question type must be one of: {valid_question_types}",
                required_for_intent=TaskIntent.INFO
            ))
        
        return errors
    
    def _build_normalized_task(self, task_data: dict, intent: TaskIntent) -> CallTask:
        """Build normalized CallTask from validated data."""
        
        # Build business info
        business_data = task_data["business"]
        business = BusinessInfo(
            phone=self._normalize_phone(business_data["phone"]),
            name=business_data.get("name", ""),
            timezone=business_data.get("timezone", "UTC"),
            website=business_data.get("website"),
            address=business_data.get("address")
        )
        
        # Build user info
        user_data = task_data["user"]
        user = UserInfo(
            name=user_data["name"],
            callback_phone=self._normalize_phone(user_data.get("callback_phone")) if user_data.get("callback_phone") else None,
            email=user_data.get("email")
        )
        
        # Build policy
        policy_data = task_data.get("policy", {})
        policy = CallPolicy(
            autonomy_level=policy_data.get("autonomy_level", "medium"),
            max_call_duration_minutes=policy_data.get("max_call_duration_minutes", 4),
            allow_payment_info=policy_data.get("allow_payment_info", False),
            allow_personal_details=policy_data.get("allow_personal_details", True),
            disclosure_allowlist=policy_data.get("disclosure_allowlist", []),
            max_retries=policy_data.get("max_retries", 2)
        )
        
        # Build intent-specific payload
        reservation = None
        reschedule = None
        cancel = None
        info = None
        
        if intent == TaskIntent.RESERVE:
            reservation = self._build_reservation_task(task_data["reservation"])
        elif intent == TaskIntent.RESCHEDULE:
            reschedule = self._build_reschedule_task(task_data["reschedule"])
        elif intent == TaskIntent.CANCEL:
            cancel = self._build_cancel_task(task_data["cancel"])
        elif intent == TaskIntent.INFO:
            info = self._build_info_task(task_data["info"])
        
        # Generate idempotency key
        idempotency_key = self._generate_idempotency_key(task_data, intent)
        
        return CallTask(
            business=business,
            user=user,
            intent=intent,
            locale=task_data.get("locale", "en-US"),
            policy=policy,
            reservation=reservation,
            reschedule=reschedule,
            cancel=cancel,
            info=info,
            idempotency_key=idempotency_key,
            task_id=task_data.get("task_id"),
            created_at=datetime.utcnow()
        )
    
    def _build_reservation_task(self, reservation_data: dict) -> ReservationTask:
        """Build ReservationTask from data."""
        date = self._parse_datetime(reservation_data["date"])
        
        time_window_data = reservation_data["time_window"]
        time_window = TimeWindow(
            start_time=self._parse_time(time_window_data["start_time"]),
            end_time=self._parse_time(time_window_data["end_time"]),
            date=date
        )
        
        return ReservationTask(
            date=date,
            time_window=time_window,
            party_size=int(reservation_data["party_size"]),
            notes=reservation_data.get("notes"),
            budget_range=reservation_data.get("budget_range"),
            special_requests=reservation_data.get("special_requests")
        )
    
    def _build_reschedule_task(self, reschedule_data: dict) -> RescheduleTask:
        """Build RescheduleTask from data."""
        new_date = self._parse_datetime(reschedule_data["new_date"])
        
        time_window_data = reschedule_data["new_time_window"]
        new_time_window = TimeWindow(
            start_time=self._parse_time(time_window_data["start_time"]),
            end_time=self._parse_time(time_window_data["end_time"]),
            date=new_date
        )
        
        return RescheduleTask(
            booking_reference=reschedule_data.get("booking_reference"),
            disambiguation_bundle=reschedule_data.get("disambiguation_bundle"),
            new_date=new_date,
            new_time_window=new_time_window
        )
    
    def _build_cancel_task(self, cancel_data: dict) -> CancelTask:
        """Build CancelTask from data."""
        return CancelTask(
            booking_reference=cancel_data.get("booking_reference"),
            disambiguation_bundle=cancel_data.get("disambiguation_bundle"),
            name_on_reservation=cancel_data.get("name_on_reservation"),
            cancellation_reason=cancel_data.get("cancellation_reason")
        )
    
    def _build_info_task(self, info_data: dict) -> InfoTask:
        """Build InfoTask from data."""
        return InfoTask(
            question_type=info_data["question_type"],
            context=info_data.get("context"),
            specific_date=self._parse_datetime(info_data.get("specific_date")) if info_data.get("specific_date") else None,
            party_size=info_data.get("party_size")
        )
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format (E.164)."""
        return bool(self.phone_pattern.match(phone))
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to E.164 format."""
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Add + if missing
        if not cleaned.startswith('+'):
            if len(cleaned) == 10:
                # US number
                cleaned = '+1' + cleaned
            elif len(cleaned) == 11 and cleaned.startswith('1'):
                # US number with country code
                cleaned = '+' + cleaned
            elif len(cleaned) == 11 and cleaned.startswith('0'):
                # German mobile number starting with 0 (0170...)
                cleaned = '+49' + cleaned[1:]  # Remove leading 0, add +49
            elif len(cleaned) == 10 and cleaned.startswith('17'):
                # German mobile number without country code (170...)
                cleaned = '+49' + cleaned
            else:
                # Default: assume it needs a + prefix
                cleaned = '+' + cleaned
        
        return cleaned
    
    def _parse_datetime(self, date_str: str) -> datetime:
        """Parse datetime string in ISO format."""
        if isinstance(date_str, datetime):
            return date_str
        
        # Try ISO format first
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            # Try common formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date: {date_str}")
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string in HH:MM format."""
        if isinstance(time_str, time):
            return time_str
        
        match = self.time_pattern.match(time_str)
        if not match:
            raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM")
        
        hour, minute = map(int, match.groups())
        return time(hour, minute)
    
    def _generate_idempotency_key(self, task_data: dict, intent: TaskIntent) -> str:
        """Generate idempotency key from task data."""
        # Create a deterministic hash from key fields
        key_fields = {
            "intent": intent.value,
            "business_phone": task_data["business"]["phone"],
            "user_name": task_data["user"]["name"]
        }
        
        # Add intent-specific fields
        if intent == TaskIntent.RESERVE:
            reservation = task_data.get("reservation", {})
            key_fields.update({
                "date": reservation.get("date"),
                "party_size": reservation.get("party_size"),
                "time_window": reservation.get("time_window")
            })
        elif intent == TaskIntent.RESCHEDULE:
            reschedule = task_data.get("reschedule", {})
            key_fields.update({
                "booking_ref": reschedule.get("booking_reference"),
                "new_date": reschedule.get("new_date")
            })
        elif intent == TaskIntent.CANCEL:
            cancel = task_data.get("cancel", {})
            key_fields.update({
                "booking_ref": cancel.get("booking_reference"),
                "name": cancel.get("name_on_reservation")
            })
        
        # Create hash
        key_string = "|".join(f"{k}:{v}" for k, v in sorted(key_fields.items()) if v is not None)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
