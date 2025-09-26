"""
Post-call outcome handler.

Processes webhook payloads from ElevenLabs and normalizes them to standard status vocabulary.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, time
import re

from .contracts import (
    CallResult, CallStatus, NextAction, CallArtifact, 
    CallObservations, CallEvidence
)
from .outbound_caller import caller
from .observability import ObservabilityLogger


class PostCallHandler:
    """Handles post-call webhook processing and normalization."""
    
    def __init__(self):
        self.logger = ObservabilityLogger()
        
        # Status mapping patterns for webhook processing
        self.status_patterns = {
            CallStatus.COMPLETED: [
                r"successfully.*reserv", r"booked.*table", r"confirmed.*appointment",
                r"reservation.*confirmed", r"appointment.*scheduled", r"cancelled.*successfully"
            ],
            CallStatus.NO_AVAILABILITY: [
                r"no.*availability", r"fully.*booked", r"no.*slots", r"no.*tables",
                r"booked.*up", r"unavailable"
            ],
            CallStatus.NO_ANSWER: [
                r"no.*answer", r"busy.*signal", r"not.*picked.*up", r"ringing.*no.*answer"
            ],
            CallStatus.VOICEMAIL: [
                r"voicemail", r"voice.*mail", r"left.*message", r"recorded.*message"
            ],
            CallStatus.IVR_BLOCKED: [
                r"ivr", r"automated.*system", r"press.*1", r"menu.*options",
                r"automated.*menu", r"cannot.*connect.*to.*human"
            ],
            CallStatus.NEEDS_USER_INPUT: [
                r"need.*more.*information", r"missing.*details", r"require.*confirmation",
                r"need.*to.*speak.*to.*user", r"insufficient.*information"
            ],
            CallStatus.TIMEOUT: [
                r"timeout", r"call.*ended", r"maximum.*duration", r"call.*limit"
            ]
        }
    
    def process_webhook(self, webhook_payload: Dict[str, Any]) -> CallResult:
        """
        Process ElevenLabs webhook payload and return normalized result.
        
        Args:
            webhook_payload: Raw webhook data from ElevenLabs
            
        Returns:
            Normalized CallResult
        """
        self.logger.log_webhook_processing_started(webhook_payload)
        
        try:
            # Handle ElevenLabs webhook format
            if "type" in webhook_payload and webhook_payload["type"] == "post_call_transcription":
                # ElevenLabs format: extract data from nested structure
                envelope = webhook_payload
                data = envelope.get("data", {}) or {}
                call_id = data.get("conversation_id") or data.get("call_id")
                status_text = str(data.get("status", ""))
                
                # Extract transcript summary from analysis
                analysis = data.get("analysis", {}) or {}
                summary = (
                    analysis.get("transcript_summary")
                    if isinstance(analysis, dict)
                    else ""
                ) or str(data.get("summary", ""))
                
                # Debug logging for analysis and summary
                self.logger._log_event(
                    level="DEBUG",
                    event_type="analysis_debug",
                    message="Processing analysis data",
                    metadata={
                        "analysis_type": type(analysis).__name__,
                        "analysis_keys": list(analysis.keys()) if isinstance(analysis, dict) else "not_dict",
                        "summary_type": type(summary).__name__,
                        "summary_value": str(summary)[:100] if summary else "empty"
                    },
                    correlation_id=call_id
                )
                
                # Extract full transcript text
                transcript_turns = data.get("transcript", []) or []
                
                # Debug logging for transcript structure
                self.logger._log_event(
                    level="DEBUG",
                    event_type="transcript_debug",
                    message="Processing transcript",
                    metadata={
                        "transcript_type": type(transcript_turns).__name__,
                        "transcript_length": len(transcript_turns) if isinstance(transcript_turns, list) else "not_list",
                        "first_item_type": type(transcript_turns[0]).__name__ if transcript_turns and isinstance(transcript_turns, list) else "none",
                        "first_item_sample": str(transcript_turns[0])[:100] if transcript_turns and isinstance(transcript_turns, list) else "none"
                    },
                    correlation_id=call_id
                )
                
                transcript = self._extract_transcript_text(transcript_turns)
                
                # Debug logging for transcript result
                self.logger._log_event(
                    level="DEBUG",
                    event_type="transcript_extraction_debug",
                    message="Transcript extraction completed",
                    metadata={
                        "transcript_type": type(transcript).__name__,
                        "transcript_length": len(transcript) if isinstance(transcript, str) else "not_string",
                        "transcript_preview": transcript[:200] if isinstance(transcript, str) else str(transcript)[:200]
                    },
                    correlation_id=call_id
                )
                
                # Log the actual conversation turns for debugging
                self.logger._log_event(
                    level="INFO",
                    event_type="transcript_structure_debug",
                    message="Transcript structure analysis",
                    metadata={
                        "conversation_id": call_id,
                        "transcript_turns_type": type(transcript_turns).__name__,
                        "transcript_turns_length": len(transcript_turns) if isinstance(transcript_turns, list) else "not_list",
                        "first_turn_sample": str(transcript_turns[0]) if transcript_turns and isinstance(transcript_turns, list) else "none",
                        "first_turn_keys": list(transcript_turns[0].keys()) if transcript_turns and isinstance(transcript_turns, list) and isinstance(transcript_turns[0], dict) else "not_dict"
                    },
                    correlation_id=call_id
                )
                
                if isinstance(transcript_turns, list) and transcript_turns:
                    self.logger._log_event(
                        level="INFO",
                        event_type="conversation_transcript",
                        message="Full conversation transcript",
                        metadata={
                            "conversation_id": call_id,
                            "total_turns": len(transcript_turns),
                            "transcript_turns": [
                                {
                                    "role": turn.get("role", "unknown") if isinstance(turn, dict) else "not_dict",
                                    "text": (turn.get("text") or turn.get("message", "")) if isinstance(turn, dict) else str(turn),
                                    "timestamp": turn.get("timestamp", "") if isinstance(turn, dict) else ""
                                } for turn in transcript_turns[:10]  # Limit to first 10 turns for logging
                            ]
                        },
                        correlation_id=call_id
                    )
                
                # Build enriched payload for downstream processing
                metadata = data.get("metadata", {}) or {}
                enriched_data = dict(data)
                enriched_data["summary"] = summary or ""
                enriched_data["transcript"] = transcript or ""
                enriched_data["raw_transcript_turns"] = transcript_turns
                enriched_data["analysis"] = analysis
                enriched_data["metadata"] = metadata
                enriched_data["event_timestamp"] = envelope.get("event_timestamp")
                enriched_data["type"] = envelope.get("type")
                if call_id and "call_id" not in enriched_data:
                    enriched_data["call_id"] = call_id
                if metadata:
                    if "call_duration_secs" in metadata and "duration_seconds" not in enriched_data:
                        enriched_data["duration_seconds"] = metadata.get("call_duration_secs")
                    if "cost" in metadata and "cost" not in enriched_data:
                        enriched_data["cost"] = metadata.get("cost")
                enriched_data["raw_envelope"] = envelope
                
                full_data = enriched_data
                status_text = status_text.lower()
            else:
                # Legacy format or direct data
                call_id = webhook_payload.get("call_id")
                status_text = str(webhook_payload.get("status", "")).lower()
                summary = webhook_payload.get("summary", "")
                transcript = webhook_payload.get("transcript", "")
                full_data = webhook_payload
            
            # Debug logging before status determination
            self.logger._log_event(
                level="DEBUG",
                event_type="status_determination_debug",
                message="About to determine status",
                metadata={
                    "status_text_type": type(status_text).__name__,
                    "status_text_value": str(status_text),
                    "summary_type": type(summary).__name__,
                    "summary_value": str(summary)[:100],
                    "transcript_type": type(transcript).__name__,
                    "transcript_value": str(transcript)[:100]
                },
                correlation_id=call_id
            )
            
            # Determine normalized status
            status = self._determine_status(status_text, summary, transcript)
            
            # Extract artifacts and observations
            artifact = self._extract_artifact(full_data, status)
            observations = self._extract_observations(full_data, status)
            
            # Determine next action
            next_action = self._determine_next_action(status, artifact, observations)
            
            # Build evidence
            evidence = self._build_evidence(full_data)
            
            # Generate human-readable message
            message = self._generate_message(status, artifact, observations)
            
            # Get call info for correlation
            call_info = caller.get_call_info(call_id) if call_id else None
            
            result = CallResult(
                status=status,
                core_artifact=artifact,
                observations=observations,
                next_action=next_action,
                evidence=evidence,
                message=message,
                call_id=call_id,
                task_id=call_info.get("task_id") if call_info else None,
                idempotency_key=call_info.get("idempotency_key") if call_info else None,
                completed_at=datetime.utcnow()
            )
            
            # Update call tracking
            if call_id:
                if status == CallStatus.COMPLETED:
                    caller.complete_call(call_id, result.__dict__)
                else:
                    caller.fail_call(call_id, status.value)
            
            self.logger.log_webhook_processing_completed(result)
            return result
            
        except Exception as e:
            self.logger.log_webhook_processing_error(str(e))
            # Return error result
            return CallResult(
                status=CallStatus.ERROR,
                message=f"Failed to process webhook: {str(e)}",
                call_id=webhook_payload.get("call_id"),
                completed_at=datetime.utcnow()
            )
    
    def _determine_status(self, status_text: str, summary: str, transcript: str) -> CallStatus:
        """Determine normalized status from webhook data."""
        # Ensure all inputs are strings
        status_text = str(status_text) if status_text else ""
        summary = str(summary) if summary else ""
        transcript = str(transcript) if transcript else ""
        
        combined_text = f"{status_text} {summary} {transcript}".lower()
        
        # Check for each status pattern
        for status, patterns in self.status_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    return status
        
        # Default to completed if no specific patterns match and status suggests success
        if any(word in combined_text for word in ["success", "complete", "done", "finished"]):
            return CallStatus.COMPLETED
        
        # Default to error for unrecognized states
        return CallStatus.ERROR
    
    def _extract_artifact(self, webhook_payload: Dict[str, Any], status: CallStatus) -> Optional[CallArtifact]:
        """Extract core artifact from webhook data."""
        if status != CallStatus.COMPLETED:
            return None
        
        summary = webhook_payload.get("summary", "")
        transcript = webhook_payload.get("transcript", "")
        
        # Ensure summary and transcript are strings
        summary = str(summary) if summary else ""
        transcript = str(transcript) if transcript else ""
        
        artifact = CallArtifact()
        
        # Extract booking reference
        booking_ref_pattern = r"(?:booking|confirmation|reference).*?(?:number|code|id).*?(\w+)"
        booking_match = re.search(booking_ref_pattern, summary + " " + transcript, re.IGNORECASE)
        if booking_match:
            artifact.booking_reference = booking_match.group(1)
        
        # Extract date and time
        date_pattern = r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})"
        time_pattern = r"(\d{1,2}:\d{2})\s*(?:am|pm)?"
        
        date_match = re.search(date_pattern, summary + " " + transcript)
        if date_match:
            try:
                artifact.confirmed_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            except ValueError:
                try:
                    artifact.confirmed_date = datetime.strptime(date_match.group(1), "%m/%d/%Y")
                except ValueError:
                    pass
        
        time_match = re.search(time_pattern, summary + " " + transcript, re.IGNORECASE)
        if time_match:
            try:
                artifact.confirmed_time = datetime.strptime(time_match.group(1), "%H:%M").time()
            except ValueError:
                pass
        
        # Extract party size
        party_pattern = r"(?:party|group|people|guests).*?(\d+)"
        party_match = re.search(party_pattern, summary + " " + transcript, re.IGNORECASE)
        if party_match:
            artifact.party_size = int(party_match.group(1))
        
        # Extract cost information
        cost_pattern = r"\$(\d+(?:\.\d{2})?)"
        cost_match = re.search(cost_pattern, summary + " " + transcript)
        if cost_match:
            artifact.total_cost = f"${cost_match.group(1)}"
        
        # Extract confirmation code
        code_pattern = r"(?:confirmation|code).*?([A-Z0-9]{4,8})"
        code_match = re.search(code_pattern, summary + " " + transcript, re.IGNORECASE)
        if code_match:
            artifact.confirmation_code = code_match.group(1)
        
        return artifact
    
    def _extract_observations(self, webhook_payload: Dict[str, Any], status: CallStatus) -> Optional[CallObservations]:
        """Extract observations and additional information."""
        summary = webhook_payload.get("summary", "")
        transcript = webhook_payload.get("transcript", "")
        
        # Ensure summary and transcript are strings
        summary = str(summary) if summary else ""
        transcript = str(transcript) if transcript else ""
        
        combined_text = f"{summary} {transcript}".lower()
        
        observations = CallObservations()
        
        # Extract offered alternatives
        alt_patterns = [
            r"alternative.*?(?:time|date|slot).*?(\d{1,2}:\d{2}|\d{1,2}/\d{1,2})",
            r"suggest.*?(?:time|date|slot).*?(\d{1,2}:\d{2}|\d{1,2}/\d{1,2})",
            r"available.*?(?:time|date|slot).*?(\d{1,2}:\d{2}|\d{1,2}/\d{1,2})"
        ]
        
        for pattern in alt_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            observations.offered_alternatives.extend(matches)
        
        # Extract online booking hints
        online_patterns = [
            r"book.*online", r"website.*booking", r"online.*reservation",
            r"visit.*website", r"check.*online"
        ]
        
        for pattern in online_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                observations.online_booking_hints.append("Book online available")
        
        # Extract business hours
        hours_pattern = r"(?:hours|open).*?(\d{1,2}:\d{2}.*?\d{1,2}:\d{2})"
        hours_match = re.search(hours_pattern, combined_text, re.IGNORECASE)
        if hours_match:
            observations.business_hours = hours_match.group(1)
        
        # Extract cancellation policy
        cancel_pattern = r"(?:cancel|cancellation).*?(?:policy|24.*hours|48.*hours)"
        if re.search(cancel_pattern, combined_text, re.IGNORECASE):
            observations.cancellation_policy = "Cancellation policy mentioned"
        
        # Extract payment methods
        payment_patterns = [
            r"cash.*only", r"credit.*card", r"debit.*card", r"cash.*or.*card"
        ]
        
        for pattern in payment_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                observations.payment_methods.append(pattern.replace(".*", " "))
        
        return observations if any([
            observations.offered_alternatives,
            observations.online_booking_hints,
            observations.business_hours,
            observations.cancellation_policy,
            observations.payment_methods
        ]) else None
    
    def _determine_next_action(self, status: CallStatus, artifact: Optional[CallArtifact], 
                              observations: Optional[CallObservations]) -> NextAction:
        """Determine recommended next action based on status and results."""
        if status == CallStatus.COMPLETED and artifact:
            return NextAction.ADD_TO_CALENDAR
        
        if status == CallStatus.NO_ANSWER:
            return NextAction.RETRY_LATER
        
        if status == CallStatus.NEEDS_USER_INPUT:
            return NextAction.REQUEST_USER_INPUT
        
        if status == CallStatus.IVR_BLOCKED:
            return NextAction.SWITCH_CHANNEL
        
        if status in [CallStatus.NO_AVAILABILITY, CallStatus.VOICEMAIL]:
            return NextAction.RETRY_LATER
        
        return NextAction.NONE
    
    def _build_evidence(self, webhook_payload: Dict[str, Any]) -> CallEvidence:
        """Build evidence object from webhook data."""
        metadata = webhook_payload.get("metadata") if isinstance(webhook_payload, dict) else None
        call_duration = webhook_payload.get("duration_seconds") if isinstance(webhook_payload, dict) else None
        if call_duration is None and isinstance(metadata, dict):
            call_duration = metadata.get("call_duration_secs")
        raw_envelope = (
            webhook_payload.get("raw_envelope")
            if isinstance(webhook_payload, dict)
            else None
        )
        return CallEvidence(
            provider_call_id=webhook_payload.get("conversation_id") or webhook_payload.get("call_id"),
            transcript_url=webhook_payload.get("transcript_url"),
            recording_url=webhook_payload.get("recording_url"),
            call_duration_seconds=call_duration,
            webhook_payload=raw_envelope or webhook_payload
        )
    
    def _generate_message(self, status: CallStatus, artifact: Optional[CallArtifact], 
                         observations: Optional[CallObservations]) -> str:
        """Generate human-readable summary message."""
        if status == CallStatus.COMPLETED:
            if artifact and artifact.booking_reference:
                return f"Successfully completed task. Booking reference: {artifact.booking_reference}"
            return "Task completed successfully"
        
        if status == CallStatus.NO_AVAILABILITY:
            if observations and observations.offered_alternatives:
                return f"No availability for requested time. Alternatives: {', '.join(observations.offered_alternatives)}"
            return "No availability for requested time"
        
        if status == CallStatus.NO_ANSWER:
            return "Business did not answer the phone"
        
        if status == CallStatus.VOICEMAIL:
            return "Call went to voicemail"
        
        if status == CallStatus.IVR_BLOCKED:
            return "Could not reach a human representative"
        
        if status == CallStatus.NEEDS_USER_INPUT:
            return "Need additional information from user to complete task"
        
        if status == CallStatus.TIMEOUT:
            return "Call timed out"
        
        if status == CallStatus.ERROR:
            return "An error occurred during the call"
        
        return "Call completed with unknown status"
    
    def _extract_transcript_text(self, transcript_turns: List[Dict[str, Any]]) -> str:
        """Extract full transcript text from ElevenLabs transcript turns."""
        if not transcript_turns:
            return ""
        
        transcript_parts = []
        for turn in transcript_turns:
            if isinstance(turn, dict):
                speaker = (
                    turn.get("speaker")
                    or turn.get("role")
                    or "unknown"
                )
                text = turn.get("text") or turn.get("message", "")
                if text:
                    transcript_parts.append(f"{speaker}: {text}")
            elif isinstance(turn, str):
                # Handle case where transcript might be a list of strings
                transcript_parts.append(turn)
        
        return " ".join(transcript_parts)
