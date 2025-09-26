"""
Mid-call tool webhook handler.

Provides HTTP endpoints for mid-call tool requests from the ElevenLabs agent.
"""

from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
import hmac
import hashlib
import json

from .config import get_config
from .observability import ObservabilityLogger


class ToolWebhookHandler:
    """Handles mid-call tool requests."""
    
    def __init__(self):
        self.logger = ObservabilityLogger()
        self.tools = {
            "availability_lookup": self._availability_lookup,
            "calendar_hold": self._calendar_hold,
            "business_info": self._business_info
        }
    
    async def handle_tool_request(self, tool_name: str, request_data: Dict[str, Any], 
                                 request: Request) -> Dict[str, Any]:
        """
        Handle a tool request from the ElevenLabs agent.
        
        Args:
            tool_name: Name of the tool to execute
            request_data: Tool request parameters
            request: FastAPI request object for verification
            
        Returns:
            Tool response data
        """
        # Verify webhook signature if configured
        if not self._verify_webhook_signature(request):
            self.logger._log_event(
                level="WARN",
                event_type="webhook_signature_failed",
                message="Tool webhook signature verification failed",
                metadata={"tool_name": tool_name}
            )
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        self.logger._log_event(
            level="INFO",
            event_type="tool_request_received",
            message=f"Tool request received: {tool_name}",
            metadata={
                "tool_name": tool_name,
                "request_data": request_data
            }
        )
        
        # Route to appropriate tool
        if tool_name not in self.tools:
            self.logger._log_event(
                level="WARN",
                event_type="unknown_tool_requested",
                message=f"Unknown tool requested: {tool_name}",
                metadata={"tool_name": tool_name, "available_tools": list(self.tools.keys())}
            )
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        try:
            result = await self.tools[tool_name](request_data)
            
            self.logger._log_event(
                level="INFO",
                event_type="tool_request_completed",
                message=f"Tool {tool_name} completed successfully",
                metadata={
                    "tool_name": tool_name,
                    "result": result
                }
            )
            
            return result
            
        except Exception as e:
            self.logger._log_event(
                level="ERROR",
                event_type="tool_request_failed",
                message=f"Tool {tool_name} failed: {str(e)}",
                metadata={
                    "tool_name": tool_name,
                    "error": str(e)
                }
            )
            raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")
    
    def _verify_webhook_signature(self, request: Request) -> bool:
        """Verify webhook signature for security."""
        # Skip verification in development
        if get_config().service.environment == "development":
            return True
        
        # In production, verify HMAC signature
        signature = request.headers.get("X-Webhook-Signature")
        if not signature:
            return False
        
        # Get request body
        body = request.body()
        if not body:
            return False
        
        # Calculate expected signature
        expected_signature = hmac.new(
            get_config().service.webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def _availability_lookup(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Look up availability for a business.
        
        For MVP, returns hardcoded responses.
        In production, this would query a real availability system.
        """
        date = request_data.get("date", "2024-01-15")
        time_window = request_data.get("time_window", "18:00-20:00")
        party_size = request_data.get("party_size", 2)
        
        # Mock availability data
        available_slots = [
            "19:30", "20:00", "20:30"
        ]
        
        return {
            "available_slots": available_slots,
            "next_available": available_slots[0],
            "message": f"Found {len(available_slots)} available slots for {party_size} people on {date}",
            "speech_friendly": f"19:30 is free for {party_size} people"
        }
    
    async def _calendar_hold(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hold a time slot in the user's calendar.
        
        For MVP, this is a no-op that returns success.
        In production, this would create a tentative calendar event.
        """
        date = request_data.get("date", "2024-01-15")
        time = request_data.get("time", "19:30")
        duration = request_data.get("duration", 120)  # minutes
        
        # Mock calendar hold
        return {
            "ok": True,
            "hold_id": f"hold_{date}_{time}",
            "message": f"Time slot {time} on {date} held for {duration} minutes",
            "speech_friendly": "Time slot held successfully"
        }
    
    async def _business_info(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Look up business information.
        
        For MVP, returns hardcoded business details.
        In production, this would query a business directory API.
        """
        business_name = request_data.get("business_name", "Sample Restaurant")
        info_type = request_data.get("info_type", "hours")
        
        # Mock business info
        business_data = {
            "hours": "Mon-Sun: 11:00 AM - 10:00 PM",
            "phone": "+1-555-123-4567",
            "address": "123 Main St, City, State 12345",
            "website": "https://example.com",
            "price_range": "$$",
            "cuisine": "Italian"
        }
        
        if info_type in business_data:
            return {
                "info_type": info_type,
                "value": business_data[info_type],
                "message": f"{info_type.title()}: {business_data[info_type]}",
                "speech_friendly": f"The {info_type} is {business_data[info_type]}"
            }
        else:
            return {
                "info_type": info_type,
                "value": "Not available",
                "message": f"{info_type} information not available",
                "speech_friendly": f"I don't have {info_type} information available"
            }


# Global handler instance
tool_handler = ToolWebhookHandler()
