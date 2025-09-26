"""
Acceptance tests for the Calling Module.

Table-driven tests with mocks for all major scenarios.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, time, timedelta

from calling_module.contracts import (
    TaskIntent, CallStatus, NextAction, CallResult,
    CallTask, BusinessInfo, UserInfo, TimeWindow,
    ReservationTask, ValidationResult
)
from calling_module.input_adapter import InputAdapter
from calling_module.router import CallingModuleRouter
from calling_module.outbound_caller import OutboundCaller

# Test phone numbers for real call simulation
PHONE_NUMBER_JONAS = "+491706255818"  # Jonas's phone (destination)
PHONE_NUMBER_TWILIO = "+15205953159"  # Our Twilio number (source/callback)


class TestInputAdapter:
    """Test input validation and normalization."""
    
    def setup_method(self):
        self.adapter = InputAdapter()
    
    @pytest.mark.parametrize("task_data,expected_valid", [
        # Valid reservation task
        ({
            "business": {"phone": PHONE_NUMBER_JONAS, "name": "Test Restaurant"},
            "user": {"name": "John Doe"},
            "intent": "reserve",
            "reservation": {
                "date": "2024-01-15",
                "time_window": {"start_time": "19:00", "end_time": "21:00"},
                "party_size": 2,
                "notes": "Birthday dinner celebration",
                "budget_range": "$50–80 per person"
            }
        }, True),
        
        # Invalid - missing business phone
        ({
            "business": {"name": "Test Restaurant"},
            "user": {"name": "John Doe"},
            "intent": "reserve",
            "reservation": {
                "date": "2024-01-15",
                "time_window": {"start_time": "19:00", "end_time": "21:00"},
                "party_size": 2
            }
        }, False),
        
        # Invalid - missing user name
        ({
            "business": {"phone": PHONE_NUMBER_JONAS, "name": "Test Restaurant"},
            "user": {},
            "intent": "reserve",
            "reservation": {
                "date": "2024-01-15",
                "time_window": {"start_time": "19:00", "end_time": "21:00"},
                "party_size": 2
            }
        }, False),
        
        # Invalid - missing reservation details
        ({
            "business": {"phone": PHONE_NUMBER_JONAS, "name": "Test Restaurant"},
            "user": {"name": "John Doe"},
            "intent": "reserve"
        }, False),
        
        # Valid cancel task
        ({
            "business": {"phone": PHONE_NUMBER_JONAS, "name": "Test Restaurant"},
            "user": {"name": "John Doe"},
            "intent": "cancel",
            "cancel": {"booking_reference": "REF123"}
        }, True),
        
        # Valid info task
        ({
            "business": {"phone": PHONE_NUMBER_JONAS, "name": "Test Restaurant"},
            "user": {"name": "John Doe"},
            "intent": "info",
            "info": {"question_type": "availability"}
        }, True)
    ])
    def test_validate_task(self, task_data, expected_valid):
        """Test task validation with various inputs."""
        result = self.adapter.validate(task_data)
        assert result.is_valid == expected_valid
        
        if not expected_valid:
            assert len(result.errors) > 0
        else:
            assert result.normalized_task is not None
            assert result.normalized_task.intent.value == task_data["intent"]
    
    def test_phone_normalization(self):
        """Test phone number normalization to E.164 format."""
        # Test various phone formats including Jonas's German number
        test_cases = [
            ("1234567890", "+11234567890"),
            ("+1234567890", "+1234567890"),
            ("(123) 456-7890", "+11234567890"),
            ("123-456-7890", "+11234567890"),
            ("+44 20 7946 0958", "+442079460958"),
            ("+49 170 625 5818", "+491706255818"),  # Jonas's German number
            ("0170 625 5818", "+491706255818")  # German mobile without country code
        ]
        
        for input_phone, expected in test_cases:
            result = self.adapter._normalize_phone(input_phone)
            assert result == expected
    
    def test_idempotency_key_generation(self):
        """Test that idempotency keys are deterministic."""
        task_data = {
            "business": {"phone": PHONE_NUMBER_JONAS, "name": "Test Restaurant"},
            "user": {"name": "John Doe"},
            "intent": "reserve",
            "reservation": {
                "date": "2024-01-15",
                "time_window": {"start_time": "19:00", "end_time": "21:00"},
                "party_size": 2,
                "notes": "Business dinner meeting",
                "budget_range": "$40–60 per person"
            }
        }
        
        result1 = self.adapter.validate(task_data)
        result2 = self.adapter.validate(task_data)
        
        assert result1.is_valid
        assert result2.is_valid
        assert result1.normalized_task.idempotency_key == result2.normalized_task.idempotency_key


class TestOutboundCaller:
    """Test outbound call functionality."""
    
    def setup_method(self):
        self.caller = OutboundCaller()
    
    @patch('elevenlabs.client.ElevenLabs')
    @patch('calling_module.outbound_caller.get_config')
    def test_start_call_success(self, mock_get_config, mock_elevenlabs):
        """Test successful call initiation with ElevenLabs SDK."""
        # Mock config
        mock_config = Mock()
        mock_config.elevenlabs.api_key = "test_key"
        mock_get_config.return_value = mock_config
        
        # Mock ElevenLabs client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.callSid = "call_12345"
        mock_client.conversational_ai.twilio.outbound_call.return_value = mock_response
        mock_elevenlabs.return_value = mock_client
        
        call_id = self.caller.start_call(
            agent_id="test_agent",
            agent_phone_number_id="test_phone_id",
            to_number=PHONE_NUMBER_JONAS,
            from_number=PHONE_NUMBER_TWILIO,
            metadata={"test": "data"}
        )
        
        assert call_id == "call_12345"
        
        # Verify the SDK was called correctly
        mock_elevenlabs.assert_called_once_with(api_key="test_key")
        mock_client.conversational_ai.twilio.outbound_call.assert_called_once_with(
            agent_id="test_agent",
            agent_phone_number_id="test_phone_id",
            to_number=PHONE_NUMBER_JONAS,
            conversation_initiation_client_data={"test": "data"}
        )
    
    def test_call_tracking(self):
        """Test call tracking functionality."""
        # Create a mock task
        task = CallTask(
            business=BusinessInfo(phone=PHONE_NUMBER_JONAS, name="Test Restaurant"),
            user=UserInfo(name="John Doe"),
            intent=TaskIntent.RESERVE,
            reservation=ReservationTask(
                date=datetime.now(),
                time_window=TimeWindow(time(19, 0), time(21, 0)),
                party_size=2
            ),
            idempotency_key="test_key",
            task_id="task_123"
        )
        
        call_id = "call_123"
        
        # Store call info
        self.caller.store_call_info(call_id, "test_key", task)
        
        # Verify storage
        call_info = self.caller.get_call_info(call_id)
        assert call_info is not None
        assert call_info["call_id"] == call_id
        assert call_info["intent"] == "reserve"
        assert call_info["task_id"] == "task_123"
        
        # Complete call
        result = {"status": "completed"}
        self.caller.complete_call(call_id, result)
        
        # Verify completion
        assert call_id not in self.caller.get_active_calls()
        assert call_id in self.caller.get_call_history()


class TestRouterIntegration:
    """Test the main router integration."""
    
    def setup_method(self):
        self.router = CallingModuleRouter()
    
    @patch('calling_module.router.OutboundCaller')
    @patch('calling_module.router.InputAdapter')
    @patch('calling_module.router.PayloadBuilder')
    def test_start_call_integration(self, mock_payload_builder, mock_input_adapter, mock_caller):
        """Test the complete start_call flow."""
        # Setup mocks
        mock_adapter_instance = Mock()
        mock_input_adapter.return_value = mock_adapter_instance
        
        mock_payload_instance = Mock()
        mock_payload_builder.return_value = mock_payload_instance
        
        mock_caller_instance = Mock()
        mock_caller.return_value = mock_caller_instance
        
        # Mock validation result
        mock_task = Mock()
        mock_task.idempotency_key = "test_key"
        mock_task.business.phone = PHONE_NUMBER_JONAS
        mock_validation_result = ValidationResult(is_valid=True, normalized_task=mock_task)
        mock_adapter_instance.validate.return_value = mock_validation_result
        
        # Mock payload building
        mock_payload = {
            "agent_id": "test_agent",
            "agent_phone_number_id": "test_phone_id",
            "metadata": {"test": "data"},
            "from_number": PHONE_NUMBER_TWILIO
        }
        mock_payload_instance.build.return_value = mock_payload
        
        # Mock call initiation
        mock_caller_instance.start_call.return_value = "call_123"
        
        # Test data
        task_data = {
            "business": {"phone": PHONE_NUMBER_JONAS, "name": "Test Restaurant"},
            "user": {"name": "John Doe"},
            "intent": "reserve",
            "reservation": {
                "date": "2024-01-15",
                "time_window": {"start_time": "19:00", "end_time": "21:00"},
                "party_size": 2,
                "notes": "Anniversary dinner",
                "budget_range": "$60–100 per person"
            }
        }
        
        # Execute
        call_id = self.router.start_call(task_data)
        
        # Verify
        assert call_id == "call_123"
        mock_adapter_instance.validate.assert_called_once_with(task_data)
        mock_payload_instance.build.assert_called_once_with(mock_task)
        mock_caller_instance.start_call.assert_called_once_with(
            agent_id="test_agent",
            agent_phone_number_id="test_phone_id",
            to_number=PHONE_NUMBER_JONAS,
            from_number=PHONE_NUMBER_TWILIO,
            metadata={"test": "data"}
        )
    
    @patch('calling_module.router.PostCallHandler')
    def test_on_postcall_integration(self, mock_postcall_handler):
        """Test the post-call processing flow."""
        # Setup mock
        mock_handler_instance = Mock()
        mock_postcall_handler.return_value = mock_handler_instance
        
        # Mock result
        mock_result = CallResult(
            status=CallStatus.COMPLETED,
            message="Success",
            call_id="call_123"
        )
        mock_handler_instance.process_webhook.return_value = mock_result
        
        # Test data
        webhook_payload = {
            "call_id": "call_123",
            "status": "completed",
            "summary": "Reservation confirmed"
        }
        
        # Execute
        result = self.router.on_postcall(webhook_payload)
        
        # Verify
        assert result.status == CallStatus.COMPLETED
        assert result.call_id == "call_123"
        mock_handler_instance.process_webhook.assert_called_once_with(webhook_payload)

    @pytest.mark.asyncio
    async def test_wait_for_result_success(self):
        """Ensure wait_for_result resolves when notify_call_result is invoked."""
        call_id = "call_async_success"

        async def emit_result():
            await asyncio.sleep(0.01)
            self.router.notify_call_result(call_id, {"call_id": call_id, "status": "completed"})

        asyncio.create_task(emit_result())
        result = await self.router.wait_for_result(call_id, timeout=1)
        assert result["status"] == "completed"
        assert result["call_id"] == call_id

    @pytest.mark.asyncio
    async def test_wait_for_result_error(self):
        """Ensure wait_for_result propagates errors via notify_call_error."""
        call_id = "call_async_error"

        async def emit_error():
            await asyncio.sleep(0.01)
            self.router.notify_call_error(call_id, RuntimeError("call failed"))

        asyncio.create_task(emit_error())
        with pytest.raises(RuntimeError, match="call failed"):
            await self.router.wait_for_result(call_id, timeout=1)


class TestCallScenarios:
    """Test various call scenarios."""
    
    @pytest.mark.parametrize("webhook_payload,expected_status,expected_next_action", [
        # Successful reservation
        ({
            "call_id": "call_123",
            "status": "completed",
            "summary": "Successfully booked table for 2 people at 19:30",
            "transcript": "Confirmed reservation for John Doe"
        }, CallStatus.COMPLETED, NextAction.ADD_TO_CALENDAR),
        
        # No availability
        ({
            "call_id": "call_124",
            "status": "no_availability",
            "summary": "No tables available for requested time",
            "transcript": "Fully booked for that time slot"
        }, CallStatus.NO_AVAILABILITY, NextAction.RETRY_LATER),
        
        # No answer
        ({
            "call_id": "call_125",
            "status": "no_answer",
            "summary": "Phone rang but no one answered",
            "transcript": ""
        }, CallStatus.NO_ANSWER, NextAction.RETRY_LATER),
        
        # IVR blocked
        ({
            "call_id": "call_126",
            "status": "ivr_blocked",
            "summary": "Could not reach human representative",
            "transcript": "Press 1 for reservations, press 2 for..."
        }, CallStatus.IVR_BLOCKED, NextAction.SWITCH_CHANNEL),
        
        # Needs user input
        ({
            "call_id": "call_127",
            "status": "needs_input",
            "summary": "Need more information from user",
            "transcript": "Please confirm your credit card details"
        }, CallStatus.NEEDS_USER_INPUT, NextAction.REQUEST_USER_INPUT)
    ])
    def test_call_outcome_scenarios(self, webhook_payload, expected_status, expected_next_action):
        """Test various call outcome scenarios."""
        from calling_module.postcall_handler import PostCallHandler
        
        handler = PostCallHandler()
        result = handler.process_webhook(webhook_payload)
        
        assert result.status == expected_status
        assert result.next_action == expected_next_action
        assert result.call_id == webhook_payload["call_id"]


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_validation_error_handling(self):
        """Test handling of validation errors."""
        adapter = InputAdapter()
        
        # Invalid task data
        invalid_task = {
            "business": {"name": "Test Restaurant"},  # Missing phone
            "user": {},  # Missing name
            "intent": "invalid_intent"
        }
        
        result = adapter.validate(invalid_task)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        
        # Check specific error types
        error_fields = [e.field for e in result.errors]
        assert "business.phone" in error_fields or "envelope" in error_fields
        assert "user.name" in error_fields or "envelope" in error_fields
        assert "intent" in error_fields or "envelope" in error_fields
    
    @patch('elevenlabs.client.ElevenLabs')
    @patch('calling_module.outbound_caller.get_config')
    def test_call_initiation_failure(self, mock_get_config, mock_elevenlabs):
        """Test handling of call initiation failures."""
        # Mock config
        mock_config = Mock()
        mock_config.elevenlabs.api_key = "test_key"
        mock_get_config.return_value = mock_config
        
        # Mock ElevenLabs authentication error
        from elevenlabs import UnauthorizedError
        mock_elevenlabs.side_effect = UnauthorizedError("Invalid API key")
        
        caller = OutboundCaller()
        
        with pytest.raises(RuntimeError, match="ElevenLabs authentication failed"):
            caller.start_call("agent", "phone_id", PHONE_NUMBER_JONAS, PHONE_NUMBER_TWILIO, {})
    
    @patch('elevenlabs.client.ElevenLabs')
    @patch('calling_module.outbound_caller.get_config')
    def test_call_rate_limit_error(self, mock_get_config, mock_elevenlabs):
        """Test handling of rate limit errors."""
        # Mock config
        mock_config = Mock()
        mock_config.elevenlabs.api_key = "test_key"
        mock_get_config.return_value = mock_config
        
        # Mock ElevenLabs forbidden error (rate limit equivalent)
        from elevenlabs import ForbiddenError
        mock_client = Mock()
        mock_client.conversational_ai.twilio.outbound_call.side_effect = ForbiddenError("Rate limit exceeded")
        mock_elevenlabs.return_value = mock_client
        
        caller = OutboundCaller()
        
        with pytest.raises(RuntimeError, match="ElevenLabs access forbidden"):
            caller.start_call("agent", "phone_id", PHONE_NUMBER_JONAS, PHONE_NUMBER_TWILIO, {})
    
    def test_malformed_webhook_handling(self):
        """Test handling of malformed webhook payloads."""
        from calling_module.postcall_handler import PostCallHandler
        
        handler = PostCallHandler()
        
        # Malformed payload
        malformed_payload = {
            "invalid_field": "invalid_value"
        }
        
        result = handler.process_webhook(malformed_payload)
        
        # Should handle gracefully and return error status
        assert result.status == CallStatus.ERROR
        assert "Failed to process webhook" in result.message


if __name__ == "__main__":
    pytest.main([__file__])
