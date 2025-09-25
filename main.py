# main.py

import asyncio
import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

# We will import our real coordinator logic here later
# from coordinator.planner import Planner
# from coordinator.executor import Executor

app = FastAPI(
    title="Butler AI Coordinator",
    description="The central nervous system for the Butler agent.",
)

class UserRequest(BaseModel):
    user_id: str
    prompt: str

# In-memory "database" for the hackathon to see results quickly.
# Replace this with a real DB connection (Firestore, Supabase).
HACKATHON_DB = {}

async def run_coordination_logic(process_id: str, user_id: str, prompt: str):
    """
    This is the main background task where the coordinator does its work.
    """
    print(f"[{process_id}] Starting coordination for user '{user_id}' with prompt: '{prompt}'")
    
    # 1. PLAN: Generate the step-by-step plan (will be implemented next)
    print(f"[{process_id}] Generating plan...")
    await asyncio.sleep(2) # Simulate planning
    
    # 2. EXECUTE: Run the plan step-by-step (will be implemented later)
    print(f"[{process_id}] Executing plan...")
    await asyncio.sleep(5) # Simulate execution
    
    # 3. COMPLETE
    HACKATHON_DB[process_id]["status"] = "completed"
    print(f"[{process_id}] Process finished successfully.")


@app.post("/execute-task", status_code=202)
async def execute_task(request: UserRequest, background_tasks: BackgroundTasks):
    """
    Accepts a user's request and starts the coordination process in the background.
    """
    process_id = str(uuid.uuid4())
    
    # Create a record for this new process in our mock DB
    HACKATHON_DB[process_id] = {
        "process_id": process_id,
        "user_id": request.user_id,
        "prompt": request.prompt,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    background_tasks.add_task(run_coordination_logic, process_id, request.user_id, request.prompt)
    
    return {"message": "Request received. Your Butler is on it!", "process_id": process_id}

@app.get("/status/{process_id}")
async def get_status(process_id: str):
    """
    Endpoint to check the status of a running process.
    """
    if process_id not in HACKATHON_DB:
        raise HTTPException(status_code=404, detail="Process ID not found.")
    return HACKATHON_DB[process_id]