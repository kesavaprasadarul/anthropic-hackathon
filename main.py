"""
FastAPI service for the Calling Module.

Provides HTTP endpoints for the supervisor agent and webhook handlers.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import uvicorn
import hmac
import hashlib
import base64

from calling_module import start_call, on_postcall
from calling_module.tool_webhook import tool_handler
from calling_module.observability import ObservabilityLogger
from calling_module.config import get_config


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verify ElevenLabs webhook signature using HMAC-SHA256.
    
    Args:
        payload: Raw request body as string
        signature: ElevenLabs-Signature header value (format: "t=timestamp,v0=hash")
        secret: Webhook secret from ElevenLabs
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature or not secret:
        return False
    
    try:
        # Parse signature format: "t=timestamp,v0=hash"
        if ',v0=' not in signature:
            return False
        
        timestamp = signature.split(',v0=')[0][2:]  # Remove 't=' prefix
        received_hash = signature.split(',v0=')[1]
        
        # Validate timestamp (within 30 minutes)
        import time
        current_time = int(time.time())
        tolerance = 30 * 60  # 30 minutes
        if int(timestamp) < (current_time - tolerance):
            return False
        
        # Create expected signature: HMAC of "timestamp.payload"
        payload_to_sign = f"{timestamp}.{payload}"
        expected_hash = hmac.new(
            secret.encode('utf-8'),
            payload_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(received_hash, expected_hash)
        
    except (ValueError, IndexError):
        return False


# Initialize FastAPI app
app = FastAPI(
    title="Jarvis Calling Module",
    description="Outbound calling capability for multi-agent system",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize observability
logger = ObservabilityLogger()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "calling_module",
        "version": "0.1.0"
    }


@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration (remove in production)."""
    config = get_config()
    return {
        "webhook_secret_configured": bool(getattr(config.elevenlabs, 'webhook_secret', None)),
        "webhook_secret_length": len(getattr(config.elevenlabs, 'webhook_secret', '') or ''),
        "environment": config.service.environment
    }


@app.get("/metrics")
async def get_metrics():
    """Get service metrics."""
    return logger.get_metrics_summary()


@app.post("/start_call")
async def start_call_endpoint(request_data: Dict[str, Any]):
    """
    Start an outbound call.
    
    This is the main endpoint that the supervisor agent calls to initiate calls.
    """
    try:
        call_id = start_call(request_data)
        return {
            "success": True,
            "call_id": call_id,
            "message": "Call initiated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/postcall")
async def postcall_webhook(request: Request):
    """
    Post-call webhook from ElevenLabs.
    
    Processes the call outcome and returns normalized results.
    """
    try:
        # Get raw request body for signature verification
        raw_body = await request.body()
        request_data = await request.json()
        
        # Verify webhook signature if secret is configured
        config = get_config()
        webhook_secret = getattr(config.elevenlabs, 'webhook_secret', None)
        
        # Debug logging
        logger._log_event(
            level="DEBUG",
            event_type="webhook_debug",
            message="Webhook received",
            metadata={
                "webhook_secret_configured": bool(webhook_secret),
                "webhook_secret_length": len(webhook_secret or ''),
                "elevenlabs_signature_header": request.headers.get('ElevenLabs-Signature', 'missing'),
                "body_length": len(raw_body)
            },
            correlation_id=request_data.get("call_id", "unknown")
        )
        
        if webhook_secret:
            # ElevenLabs uses 'ElevenLabs-Signature' header (with capital letters)
            signature = request.headers.get('ElevenLabs-Signature', '')
            
            if signature:
                if not verify_webhook_signature(raw_body.decode('utf-8'), signature, webhook_secret):
                    logger._log_event(
                        level="WARNING",
                        event_type="webhook_signature_verification_failed",
                        message="Invalid webhook signature received",
                        metadata={
                            "signature": signature[:10] + "..." if signature else "missing",
                            "webhook_secret_length": len(webhook_secret),
                            "body_length": len(raw_body)
                        },
                        correlation_id=request_data.get("call_id", "unknown")
                    )
                    raise HTTPException(status_code=401, detail="Invalid webhook signature")
            else:
                # Temporary bypass for development - remove in production!
                if config.service.environment == "development":
                    logger._log_event(
                        level="WARNING",
                        event_type="webhook_signature_bypass",
                        message="Bypassing signature verification in development mode",
                        metadata={"reason": "No signature header found"},
                        correlation_id=request_data.get("call_id", "unknown")
                    )
                logger._log_event(
                    level="WARNING",
                    event_type="webhook_signature_verification_failed",
                    message="Invalid webhook signature received",
                    metadata={
                        "signature": signature[:10] + "..." if signature else "missing",
                        "webhook_secret_length": len(webhook_secret),
                        "body_length": len(raw_body)
                    },
                    correlation_id=request_data.get("call_id", "unknown")
                )
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Handle ElevenLabs webhook payload structure
        # ElevenLabs sends: {"type": "...", "event_timestamp": "...", "data": {...}}
        # We need to extract the actual call data from the "data" field
        actual_payload = request_data.get("data", request_data)
        
        # Debug logging for payload structure
        logger._log_event(
            level="DEBUG",
            event_type="webhook_payload_debug",
            message="Processing webhook payload",
            metadata={
                "has_data_field": "data" in request_data,
                "actual_payload_keys": list(actual_payload.keys()) if isinstance(actual_payload, dict) else "not_dict",
                "call_id_in_actual": actual_payload.get("call_id") if isinstance(actual_payload, dict) else None
            },
            correlation_id=actual_payload.get("call_id", "unknown")
        )
        
        result = on_postcall(actual_payload)
        
        # Convert result to dict for JSON response
        result_dict = {
            "status": result.status.value,
            "message": result.message,
            "next_action": result.next_action.value,
            "call_id": result.call_id,
            "task_id": result.task_id,
            "idempotency_key": result.idempotency_key,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None
        }
        
        # Add artifact if present
        if result.core_artifact:
            result_dict["core_artifact"] = {
                "booking_reference": result.core_artifact.booking_reference,
                "confirmed_date": result.core_artifact.confirmed_date.isoformat() if result.core_artifact.confirmed_date else None,
                "confirmed_time": result.core_artifact.confirmed_time.isoformat() if result.core_artifact.confirmed_time else None,
                "party_size": result.core_artifact.party_size,
                "total_cost": result.core_artifact.total_cost,
                "confirmation_code": result.core_artifact.confirmation_code
            }
        
        # Add observations if present
        if result.observations:
            result_dict["observations"] = {
                "offered_alternatives": result.observations.offered_alternatives,
                "online_booking_hints": result.observations.online_booking_hints,
                "business_hours": result.observations.business_hours,
                "cancellation_policy": result.observations.cancellation_policy,
                "payment_methods": result.observations.payment_methods
            }
        
        # Add evidence if present
        if result.evidence:
            result_dict["evidence"] = {
                "provider_call_id": result.evidence.provider_call_id,
                "call_duration_seconds": result.evidence.call_duration_seconds
                # Exclude transcript/recording URLs and webhook payload for security
            }
        
        return result_dict
        
    except Exception as e:
        logger._log_event(
            level="ERROR",
            event_type="postcall_webhook_error",
            message=f"Post-call webhook failed: {str(e)}",
            metadata={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@app.post("/tools/{tool_name}")
async def tool_webhook(tool_name: str, request_data: Dict[str, Any], request: Request):
    """
    Mid-call tool webhook.
    
    Handles tool requests from the ElevenLabs agent during calls.
    """
    try:
        result = await tool_handler.handle_tool_request(tool_name, request_data, request)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


@app.get("/tools")
async def list_available_tools():
    """List available mid-call tools."""
    return {
        "tools": [
            {
                "name": "availability_lookup",
                "description": "Look up availability for a business",
                "parameters": ["date", "time_window", "party_size"]
            },
            {
                "name": "calendar_hold",
                "description": "Hold a time slot in user's calendar",
                "parameters": ["date", "time", "duration"]
            },
            {
                "name": "business_info",
                "description": "Look up business information",
                "parameters": ["business_name", "info_type"]
            }
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=get_config().service.environment == "development",
        log_level=get_config().service.log_level.lower()
    )
