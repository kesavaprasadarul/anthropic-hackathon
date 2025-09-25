# /database/models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Any
import uuid

# ProcessStep remains the same as before
class ProcessStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    process_id: str
    step_name: str
    tool_module_name: str
    dependencies: List[Any] = []
    prompt_message: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    output_result: Optional[dict] = None
    path_name: str # We can simplify this to just 'primary' or 'recovery'

class ProcessRun(BaseModel):
    process_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    original_prompt: str
    status: Literal["pending", "running", "completed", "failed_user_error", "failed_butler_error"] = "pending"
    steps: List[ProcessStep] = []
    created_at: str
    # --- NEW FIELD ---
    # This will store a log of actions and results for the re-planner
    run_history: List[str] = []