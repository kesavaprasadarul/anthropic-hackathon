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
        
        return {
            "agent_id": self.agent_config.agent_id,
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
        
        variables = {
            "date": reservation.date.strftime("%Y-%m-%d"),
            "start_time": reservation.time_window.start_time.strftime("%H:%M"),
            "end_time": reservation.time_window.end_time.strftime("%H:%M"),
            "party_size": str(reservation.party_size)
        }
        
        if reservation.notes:
            variables["special_requests"] = reservation.notes
        
        if reservation.budget_range:
            variables["budget_range"] = reservation.budget_range
        
        return variables
    
    def _build_reschedule_variables(self, reschedule) -> Dict[str, str]:
        """Build variables for reschedule tasks."""
        if not reschedule:
            return {}
        
        variables = {
            "new_date": reschedule.new_date.strftime("%Y-%m-%d"),
            "new_start_time": reschedule.new_time_window.start_time.strftime("%H:%M"),
            "new_end_time": reschedule.new_time_window.end_time.strftime("%H:%M")
        }
        
        if reschedule.booking_reference:
            variables["booking_reference"] = reschedule.booking_reference
        
        return variables
    
    def _build_cancel_variables(self, cancel) -> Dict[str, str]:
        """Build variables for cancellation tasks."""
        if not cancel:
            return {}
        
        variables = {}
        
        if cancel.booking_reference:
            variables["booking_reference"] = cancel.booking_reference
        
        if cancel.name_on_reservation:
            variables["name_on_reservation"] = cancel.name_on_reservation
        
        if cancel.cancellation_reason:
            variables["cancellation_reason"] = cancel.cancellation_reason
        
        return variables
    
    def _build_info_variables(self, info) -> Dict[str, str]:
        """Build variables for info request tasks."""
        if not info:
            return {}
        
        variables = {
            "question_type": info.question_type
        }
        
        if info.context:
            variables["context"] = info.context
        
        if info.specific_date:
            variables["specific_date"] = info.specific_date.strftime("%Y-%m-%d")
        
        if info.party_size:
            variables["party_size"] = str(info.party_size)
        
        return variables
    
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
