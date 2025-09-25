"""
FastAPI service for the Calling Module.

Provides HTTP endpoints for the supervisor agent and webhook handlers.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import uvicorn

from calling_module import start_call, on_postcall
from calling_module.tool_webhook import tool_handler
from calling_module.observability import ObservabilityLogger
from calling_module.config import get_config


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
async def postcall_webhook(request_data: Dict[str, Any], request: Request):
    """
    Post-call webhook from ElevenLabs.
    
    Processes the call outcome and returns normalized results.
    """
    try:
        # Verify webhook signature in production
        if get_config().service.environment != "development":
            # Add signature verification here
            pass
        
        result = on_postcall(request_data)
        
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
