# /agents/contracts.py

from pydantic import BaseModel, Field
from typing import Literal, Optional

class AgentOutput(BaseModel):
    """
    Standard output structure for all agent modules.
    """
    status: Literal["completed", "failed"] = Field(
        ..., description="Indicates if the agent's task was successful."
    )
    result: Optional[str] = Field(
        None, description="A text summary of the outcome or data found."
    )
    error: Optional[str] = Field(
        None, description="A description of the error if the task failed."
    )