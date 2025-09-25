# /coordinator/executor.py

import os
import json
import asyncio
import google.generativeai as genai
from google.ai import generativelanguage as glm
from typing import List

from agents.MOCKS import mock_search_agent, mock_browser_agent, mock_calendar_agent, mock_calling_agent
from agents.contracts import AgentOutput
from database.models import ProcessStep
from .planner import Planner # Import Planner to call it for re-planning

AVAILABLE_TOOLS = {
    "mock_search_agent": mock_search_agent,
    "mock_browser_agent": mock_browser_agent,
    "mock_calendar_agent": mock_calendar_agent,
    "mock_calling_agent": mock_calling_agent,
}

class Executor:
    """
    Manages the step-by-step execution of a plan, with the ability
    to trigger a re-plan upon failure.
    """
    def __init__(self, process_id: str, original_prompt: str, run_history: List[str]):
        self.process_id = process_id
        self.original_prompt = original_prompt # Store original goal for context
        self.run_history = run_history # A log of actions for re-planning context
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash", # Using your specified model
            tools=list(AVAILABLE_TOOLS.values())
        )

    async def _execute_step(self, step: ProcessStep):
        """Executes a single step using the tool-calling ('thinking') model."""
        prompt = step.prompt_message
        print(f"\n[{self.process_id}] --- Executing Step: '{step.step_name}' ---")
        print(f"[{self.process_id}] Prompt for model: '{prompt}'")

        chat = self.model.start_chat()
        response = await chat.send_message_async(prompt)

        try:
            function_call = response.candidates[0].content.parts[0].function_call
        except (IndexError, AttributeError):
            print(f"[{self.process_id}] Model provided a direct answer.")
            # Even if the model answers directly, we wrap it in our standard AgentOutput
            return {"status": "completed", "result": response.text, "error": None}

        tool_name = function_call.name
        tool_args = dict(function_call.args) if function_call.args is not None else {}

        # --- NEW, MORE EXPLICIT CHECK ---
        if not tool_name:
            print(f"[{self.process_id}] Error: Model returned a function call with an empty name.")
            tool_result = AgentOutput(status="failed", error="Model failed to select a valid tool.")
        # --- END NEW CHECK ---
        elif tool_name in AVAILABLE_TOOLS:
            tool_function = AVAILABLE_TOOLS[tool_name]
            tool_result = await tool_function(prompt)
        else:
            print(f"[{self.process_id}] Error: Model tried to call unknown tool '{tool_name}'")
            # Note: We create an AgentOutput object here for consistency
            tool_result = AgentOutput(status="failed", error=f"Unknown tool: {tool_name}")

        print(f"[{self.process_id}] Tool Result: {tool_result}")
        
        # Send the result back to the model for a final summary
        response = await chat.send_message_async(
            content=glm.Part(function_response=glm.FunctionResponse(
                name=tool_name,
                response={"result": json.dumps(tool_result.model_dump())}
            ))
        )
        final_answer = response.candidates[0].content.parts[0].text
        print(f"[{self.process_id}] Final Answer from model: '{final_answer}'")
        
        return tool_result

    async def run(self, plan: list[ProcessStep]):
        """Runs the plan, handling failures by triggering re-planning."""
        print(f"\n[{self.process_id}] ======= STARTING DYNAMIC EXECUTION =======")
        completed_steps = {}

        # Use a while loop on the index, as the plan list can grow dynamically
        i = 0
        while i < len(plan):
            step = plan[i]
            i += 1 # Increment index before potential list modifications

            if step.status != "pending":
                continue

            if not all(dep_id in completed_steps for dep_id in step.dependencies):
                plan.append(step) # Re-queue step if dependencies not met
                continue

            step.status = "running"
            result = await self._execute_step(step)
            step.output_result = result.model_dump()
            
            # --- DYNAMIC RE-PLANNING LOGIC ---
            if result.status == "failed":
                step.status = "failed"
                self.run_history.append(f"ATTEMPTED: '{step.step_name}' but it FAILED with error: {result.error}")
                print(f"[{self.process_id}] Step '{step.step_name}' failed. Triggering re-planning...")
                
                planner = Planner(self.process_id)
                recovery_steps = await planner.generate_recovery_plan(
                    self.original_prompt, self.run_history, step
                )
                if recovery_steps:
                    print(f"[{self.process_id}] Received {len(recovery_steps)} recovery steps. Splicing into plan.")
                    # Insert the new steps right after the current one, in reverse order
                    for recovery_step in reversed(recovery_steps):
                        plan.insert(i, recovery_step)
                else:
                    print(f"[{self.process_id}] Planner did not return a recovery plan. Ending execution.")
                    break # Stop if no recovery is possible
            else:
                step.status = "completed"
                self.run_history.append(f"SUCCESS: '{step.step_name}'. Result: {result.result}")
                completed_steps[step.step_id] = result
        
        print(f"[{self.process_id}] ======== EXECUTION FINISHED ========")