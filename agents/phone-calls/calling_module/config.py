"""
Configuration management for the Calling Module.

Handles environment variables, API keys, and service configuration.
"""

import os
from typing import Optional
from dataclasses import dataclass

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
 

@dataclass
class ElevenLabsConfig:
    """ElevenLabs API configuration."""
    api_key: str
    agent_id: str  # Default/reservation agent
    agent_phone_number_id: str
    # Specialized agents for different task types
    reschedule_agent_id: Optional[str] = None
    cancel_agent_id: Optional[str] = None
    info_agent_id: Optional[str] = None
    voice_id: Optional[str] = None
    language: str = "en-US"
    webhook_secret: Optional[str] = None


@dataclass
class TwilioConfig:
    """Twilio telephony configuration."""
    account_sid: Optional[str] = None
    auth_token: Optional[str] = None
    from_number: Optional[str] = None


@dataclass
class ServiceConfig:
    """Service-level configuration."""
    webhook_secret: str
    max_call_duration_minutes: int = 5
    default_timeout_seconds: int = 100
    log_level: str = "INFO"
    environment: str = "development"


@dataclass
class CallingModuleConfig:
    """Main configuration container."""
    elevenlabs: ElevenLabsConfig
    twilio: TwilioConfig
    service: ServiceConfig


def load_config() -> CallingModuleConfig:
    """Load configuration from environment variables."""
    
    # ElevenLabs configuration
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    if not elevenlabs_api_key:
        raise ValueError("ELEVENLABS_API_KEY environment variable is required")
    
    elevenlabs_agent_id = os.getenv("ELEVENLABS_AGENT_ID")
    if not elevenlabs_agent_id:
        raise ValueError("ELEVENLABS_AGENT_ID environment variable is required")
    
    elevenlabs_agent_phone_number_id = os.getenv("ELEVENLABS_AGENT_PHONE_NUMBER_ID")
    if not elevenlabs_agent_phone_number_id:
        raise ValueError("ELEVENLABS_AGENT_PHONE_NUMBER_ID environment variable is required")
    
    elevenlabs_config = ElevenLabsConfig(
        api_key=elevenlabs_api_key,
        agent_id=elevenlabs_agent_id,
        agent_phone_number_id=elevenlabs_agent_phone_number_id,
        reschedule_agent_id=os.getenv("ELEVENLABS_RESCHEDULE_AGENT_ID"),
        cancel_agent_id=os.getenv("ELEVENLABS_CANCEL_AGENT_ID"),
        info_agent_id=os.getenv("ELEVENLABS_INFO_AGENT_ID"),
        voice_id=os.getenv("ELEVENLABS_VOICE_ID"),
        language=os.getenv("ELEVENLABS_LANGUAGE", "en-US"),
        webhook_secret=os.getenv("ELEVENLABS_WEBHOOK_SECRET")
    )
    
    # Twilio configuration (optional for managed ElevenLabs)
    twilio_config = TwilioConfig(
        account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
        from_number=os.getenv("TWILIO_FROM_NUMBER", "+15205953159")  # Default to our Twilio number
    )
    
    # Service configuration
    webhook_secret = os.getenv("WEBHOOK_SECRET", "dev-secret-change-in-production")
    service_config = ServiceConfig(
        webhook_secret=webhook_secret,
        max_call_duration_minutes=int(os.getenv("MAX_CALL_DURATION_MINUTES", "4")),
        default_timeout_seconds=int(os.getenv("DEFAULT_TIMEOUT_SECONDS", "300")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        environment=os.getenv("ENVIRONMENT", "development")
    )
    
    return CallingModuleConfig(
        elevenlabs=elevenlabs_config,
        twilio=twilio_config,
        service=service_config
    )

# Global config instance - loaded lazily
_config = None

def get_config():
    """Get the global config instance, loading it if necessary."""
    global _config
    if _config is None:
        _config = load_config()
    return _config



