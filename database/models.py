# /database/models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import uuid

class ProcessStep(BaseModel):
    """
    Represents a single step in a larger process plan.
    """
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    process_id: str
    step_name: str
    tool_module_name: str
    dependencies: List[str] = []
    input_payload: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    output_result: Optional[dict] = None
    path_name: str

class ProcessRun(BaseModel):
    """
    Represents a single, complete user request from start to finish.
    """
    process_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    original_prompt: str
    status: Literal["pending", "running", "completed", "failed_user_error", "failed_butler_error"] = "pending"
    steps: List[ProcessStep] = []
    created_at: str