# main.py (Updated)

import os
import uuid
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

# Import the new Planner
from coordinator.planner import Planner
from coordinator.executor import Executor
from database.models import ProcessRun
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Butler AI Coordinator",
    description="The central nervous system for the Butler agent.",
)

class UserRequest(BaseModel):
    user_id: str
    prompt: str

# In-memory "database" for the hackathon
HACKATHON_DB: dict[str, ProcessRun] = {}


async def run_coordination_logic(process_id: str, user_id: str, prompt: str):
    print(f"[{process_id}] Starting coordination for user '{user_id}' with prompt: '{prompt}'")
    HACKATHON_DB[process_id].status = "running"
    
    run_obj = HACKATHON_DB[process_id]
    run_obj.status = "running"
    
    # 1. PLAN: Generate the high-level strategy
    planner = Planner(process_id=process_id)
    initial_steps  = await planner.generate_initial_plan(prompt)
    
    if not initial_steps:
        print(f"[{process_id}] Planning failed. Aborting process.")
        run_obj.status = "failed_butler_error"
        return

    run_obj.steps = initial_steps
    print(f"[{process_id}] Plan Generated:")
    for step in run_obj.steps:
        print(f"  - Step: {step.step_name}, Tool: {step.tool_module_name}, Path: {step.path_name}, Prompt: {step.prompt_message}")

    # 2. EXECUTE: Use the new "thinking" Executor to run the plan
    executor = Executor(
        process_id=process_id, 
        original_prompt=prompt, 
        run_history=run_obj.run_history
    )
    await executor.run(run_obj.steps) # Pass the generated plan to the executor
    
    # 3. COMPLETE
    if all(s.status == 'completed' for s in run_obj.steps):
        run_obj.status = "completed"
    else:
        run_obj.status = "failed_butler_error"
        
    print(f"[{process_id}] Process finished with status: {run_obj.status}.")


@app.post("/execute-task", status_code=202)
async def execute_task(request: UserRequest, background_tasks: BackgroundTasks):
    """
    Accepts a user's request and starts the coordination process in the background.
    """
    process_id = str(uuid.uuid4())
    
    # Create a record for this new process using our Pydantic model
    run = ProcessRun(
        process_id=process_id,
        user_id=request.user_id,
        original_prompt=request.prompt,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    HACKATHON_DB[process_id] = run
    
    background_tasks.add_task(run_coordination_logic, process_id, request.user_id, request.prompt)
    
    return {"message": "Request received. Your Butler is on it!", "process_id": process_id}

@app.get("/status/{process_id}", response_model=ProcessRun)
async def get_status(process_id: str):
    """
    Endpoint to check the status and plan of a running process.
    """
    if process_id not in HACKATHON_DB:
        raise HTTPException(status_code=404, detail="Process ID not found.")
    return HACKATHON_DB[process_id]