"""
Payload builder for ElevenLabs agent metadata.

Builds the metadata and configuration needed for agent calls.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .contracts import CallTask, TaskIntent
from .config import get_config


class PayloadBuilder:
    """Builds payloads for ElevenLabs agent calls."""
    
    def __init__(self):
        self.agent_config = get_config().elevenlabs
        # Map task intents to specific agent IDs
        self.agent_mapping = {
            TaskIntent.RESERVE: self.agent_config.agent_id,  # Default reservation agent
            TaskIntent.RESCHEDULE: self.agent_config.reschedule_agent_id or self.agent_config.agent_id,
            TaskIntent.CANCEL: self.agent_config.cancel_agent_id or self.agent_config.agent_id,
            TaskIntent.INFO: self.agent_config.info_agent_id or self.agent_config.agent_id
        }
    
    def build(self, task: CallTask) -> Dict[str, Any]:
        """
        Build complete payload for ElevenLabs agent call.
        
        Args:
            task: Normalized call task
            
        Returns:
            Payload dictionary for agent call
        """
        # Build system prompt variables
        prompt_variables = self._build_prompt_variables(task)
        
        # Build metadata for agent
        metadata = self._build_metadata(task)
        
        # Determine voice and language
        voice_config = self._get_voice_config(task)
        
        # Select the appropriate agent for this task type
        agent_id = self.agent_mapping.get(task.intent, self.agent_config.agent_id)
        
        return {
            "agent_id": agent_id,
            "agent_phone_number_id": self.agent_config.agent_phone_number_id,
            "voice_id": voice_config["voice_id"],
            "language": voice_config["language"],
            "prompt_variables": prompt_variables,
            "metadata": metadata,
            "from_number": self._get_from_number(),
            "max_duration_seconds": task.policy.max_call_duration_minutes * 60
        }
    
    def _build_prompt_variables(self, task: CallTask) -> Dict[str, str]:
        """Build system prompt variables for the agent."""
        variables = {
            "user_name": task.user.name,
            "business_name": task.business.name,
            "intent": task.intent.value,
            "locale": task.locale,
            "autonomy_level": task.policy.autonomy_level
        }
        
        # Add intent-specific variables
        if task.intent == TaskIntent.RESERVE:
            variables.update(self._build_reservation_variables(task.reservation))
        elif task.intent == TaskIntent.RESCHEDULE:
            variables.update(self._build_reschedule_variables(task.reschedule))
        elif task.intent == TaskIntent.CANCEL:
            variables.update(self._build_cancel_variables(task.cancel))
        elif task.intent == TaskIntent.INFO:
            variables.update(self._build_info_variables(task.info))
        
        return variables
    
    def _build_reservation_variables(self, reservation) -> Dict[str, str]:
        """Build variables for reservation tasks."""
        if not reservation:
            return {}
        
        # Format date for natural conversation
        date_formatted = reservation.date.strftime("%B %d, %Y")
        time_window = f"{reservation.time_window.start_time.strftime('%I:%M %p')} to {reservation.time_window.end_time.strftime('%I:%M %p')}"
        
        # Build context summary (brief description of purpose)
        context_summary = reservation.notes or "restaurant reservation"
        
        # Build availability text (human-readable format)
        availability_text = f"{date_formatted} — {time_window}"
        
        # Calculate expected duration (default to 2 hours for restaurants)
        expected_duration = "2 hours"  # Default for restaurant reservations
        
        # Build budget range text (only mention if relevant)
        budget_range_text = f"Budget range: {reservation.budget_range}" if reservation.budget_range else ""
        budget_range_if_relevant = budget_range_text if reservation.budget_range else ""
        
        variables = {
            "date": date_formatted,
            "date_iso": reservation.date.strftime("%Y-%m-%d"),
            "start_time": reservation.time_window.start_time.strftime("%H:%M"),
            "end_time": reservation.time_window.end_time.strftime("%H:%M"),
            "time_window": time_window,
            "availability_text": availability_text,  # New format for the prompt
            "party_size": str(reservation.party_size),
            "context_summary": context_summary,  # Brief description of purpose
            "notes": reservation.notes or "",  # Separate notes field
            "budget_range": reservation.budget_range or "",  # Separate budget field
            "budget_range_if_relevant": budget_range_if_relevant,  # Conditional display
            "expected_duration": expected_duration  # Duration for this booking type
        }
        
        # Keep legacy variables for backward compatibility
        if reservation.notes:
            variables["special_requests"] = reservation.notes
        
        if reservation.budget_range:
            variables["budget_range"] = reservation.budget_range
        
        return variables
    
    def _build_reschedule_variables(self, reschedule) -> Dict[str, str]:
        """Build variables for reschedule tasks."""
        if not reschedule:
            return {}
        
        # Build context summary (brief description of booking type)
        context_summary = "reservation"  # Default, could be enhanced based on business type
        
        # Build current date text (original reservation date and time)
        current_date_text = f"{reschedule.current_date.strftime('%B %d, %Y')}"
        if hasattr(reschedule, 'current_time_window') and reschedule.current_time_window:
            current_time = f"{reschedule.current_time_window.start_time.strftime('%I:%M %p')} to {reschedule.current_time_window.end_time.strftime('%I:%M %p')}"
            current_date_text += f" at {current_time}"
        
        # Build new availability text (human-readable format)
        new_date_formatted = reschedule.new_date.strftime("%B %d, %Y")
        new_time_window = f"{reschedule.new_time_window.start_time.strftime('%I:%M %p')} to {reschedule.new_time_window.end_time.strftime('%I:%M %p')}"
        new_availability_text = f"{new_date_formatted} — {new_time_window}"
        
        # Calculate expected duration (default to 2 hours for most bookings)
        expected_duration = "2 hours"  # Default for most booking types
        
        # Build budget range text (only mention if relevant)
        budget_range_text = f"Budget range: {reschedule.budget_range}" if reschedule.budget_range else ""
        budget_range_if_relevant = budget_range_text if reschedule.budget_range else ""
        
        variables = {
            "context_summary": context_summary,  # Brief description of booking type
            "booking_reference": reschedule.booking_reference or "",  # Identifier for reservation
            "current_date": current_date_text,  # Original reservation date and time
            "new_availability_text": new_availability_text,  # Human-readable new time windows
            "notes": reschedule.notes or "",  # Preferences or constraints
            "budget_range": reschedule.budget_range or "",  # Budget range (only if asked)
            "expected_duration": expected_duration  # Duration appropriate for booking type
        }
        
        # Keep legacy variables for backward compatibility
        variables.update({
            "new_date": reschedule.new_date.strftime("%Y-%m-%d"),
            "new_start_time": reschedule.new_time_window.start_time.strftime("%H:%M"),
            "new_end_time": reschedule.new_time_window.end_time.strftime("%H:%M")
        })
        
        return variables
    
    def _build_cancel_variables(self, cancel) -> Dict[str, str]:
        """Build variables for cancellation tasks."""
        if not cancel:
            return {}
        
        # Build context summary (brief description of booking type)
        context_summary = "reservation"  # Default, could be enhanced based on business type
        
        # Build current date text (original reservation date and time)
        current_date_text = ""
        if cancel.current_date:
            current_date_text = f"{cancel.current_date.strftime('%B %d, %Y')}"
            if cancel.current_time_window:
                current_time = f"{cancel.current_time_window.start_time.strftime('%I:%M %p')} to {cancel.current_time_window.end_time.strftime('%I:%M %p')}"
                current_date_text += f" at {current_time}"
        
        variables = {
            "context_summary": context_summary,  # Brief description of booking type
            "booking_reference": cancel.booking_reference or "",  # Identifier for reservation
            "name_on_reservation": cancel.name_on_reservation or "",  # Name under which booking was made
            "current_date": current_date_text,  # Original reservation date and time
            "notes": cancel.notes or "",  # Additional details or preferences
            "cancellation_reason": cancel.cancellation_reason or ""  # Reason for cancellation (legacy)
        }
        
        return variables
    
    def _build_info_variables(self, info) -> Dict[str, str]:
        """Build variables for info request tasks."""
        if not info:
            return {}
        
        # Build context summary based on question type and context
        context_summary = self._build_info_context_summary(info)
        
        variables = {
            "context_summary": context_summary,  # Short description of the request
            "question_type": info.question_type,  # Type of information requested
            "context": info.context or "",  # Free-form details to clarify the question
            "notes": info.notes or "",  # Any preferences or additional info
            "specific_date": info.specific_date.strftime("%Y-%m-%d") if info.specific_date else "",  # Legacy support
            "party_size": str(info.party_size) if info.party_size else ""  # Legacy support
        }
        
        return variables
    
    def _build_info_context_summary(self, info) -> str:
        """Build context summary for info requests."""
        if not info:
            return "information request"
        
        # Build context summary based on question type
        base_summary = {
            "availability": "check availability",
            "status": "check reservation status", 
            "hours": "check business hours",
            "price": "check pricing information",
            "policies": "check policies"
        }.get(info.question_type, "information request")
        
        # Add party size if available
        if info.party_size:
            base_summary += f" for {info.party_size} people"
        
        # Add specific date if available
        if info.specific_date:
            date_str = info.specific_date.strftime("%B %d, %Y")
            base_summary += f" on {date_str}"
        
        return base_summary
    
    def _build_metadata(self, task: CallTask) -> Dict[str, Any]:
        """Build minimal metadata for agent decision-making."""
        metadata = {
            "task_id": task.task_id,
            "idempotency_key": task.idempotency_key,
            "intent": task.intent.value,
            "locale": task.locale,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "policy": {
                "autonomy_level": task.policy.autonomy_level,
                "allow_payment_info": task.policy.allow_payment_info,
                "allow_personal_details": task.policy.allow_personal_details,
                "max_retries": task.policy.max_retries
            }
        }
        
        # Add intent-specific metadata
        if task.intent == TaskIntent.RESERVE and task.reservation:
            metadata["reservation"] = {
                "date": task.reservation.date.isoformat(),
                "party_size": task.reservation.party_size,
                "has_notes": bool(task.reservation.notes),
                "has_budget": bool(task.reservation.budget_range)
            }
        elif task.intent == TaskIntent.RESCHEDULE and task.reschedule:
            metadata["reschedule"] = {
                "has_booking_ref": bool(task.reschedule.booking_reference),
                "new_date": task.reschedule.new_date.isoformat()
            }
        elif task.intent == TaskIntent.CANCEL and task.cancel:
            metadata["cancel"] = {
                "has_booking_ref": bool(task.cancel.booking_reference),
                "has_name": bool(task.cancel.name_on_reservation)
            }
        elif task.intent == TaskIntent.INFO and task.info:
            metadata["info"] = {
                "question_type": task.info.question_type,
                "has_context": bool(task.info.context),
                "has_specific_date": bool(task.info.specific_date)
            }
        
        return metadata
    
    def _get_voice_config(self, task: CallTask) -> Dict[str, str]:
        """Determine voice and language configuration."""
        # Default voice from config
        voice_id = self.agent_config.voice_id
        
        # Override based on locale if needed
        if task.locale.startswith("de"):
            voice_id = "voice_german"  # Placeholder - use actual German voice ID
        elif task.locale.startswith("es"):
            voice_id = "voice_spanish"  # Placeholder - use actual Spanish voice ID
        elif task.locale.startswith("fr"):
            voice_id = "voice_french"  # Placeholder - use actual French voice ID
        
        return {
            "voice_id": voice_id or "default_voice",
            "language": task.locale
        }
    
    def _get_from_number(self) -> Optional[str]:
        """Get the from number for outbound calls."""
        # Use Twilio config if available, otherwise let ElevenLabs handle it
        if get_config().twilio.from_number:
            return get_config().twilio.from_number
        return None
