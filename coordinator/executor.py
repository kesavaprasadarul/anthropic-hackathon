# /coordinator/executor.py

import os
import json
import asyncio
from typing import List, Dict, Any, Optional

from litellm import acompletion  # async, provider-agnostic chat API

from agents.MOCKS import mock_search_agent, mock_browser_agent, mock_calendar_agent, mock_calling_agent, AgentOutput
import agents.web_search.booking_agent as booking_agent
import agents.web_search.search_agent as search_agent
from database.models import ProcessStep
from .planner import Planner

BOOKING_AGENT = booking_agent.BookingAgent()
SEARCH_AGENT = search_agent.PlaceSearchAgent()

AVAILABLE_TOOLS = {
    "mock_search_agent": SEARCH_AGENT.search,
    "mock_browser_agent": mock_browser_agent,
    "mock_booking_agent": BOOKING_AGENT.create_appointment,
    "mock_availability_agent": BOOKING_AGENT.check_availability,
    "mock_calling_agent": mock_calling_agent,
}

class Executor:
    def __init__(self, process_id: str, original_prompt: str, run_history: List[str]):
        self.process_id = process_id
        self.original_prompt = original_prompt
        self.run_history = run_history
        self.model_name = os.getenv("MODEL_NAME", "anthropic/claude-3-haiku-20240307")

    async def _execute_step(self, step: ProcessStep, context: str) -> AgentOutput:
        prompt = f"Context from previous steps:\n{context}\n\nYour task now:\n{step.prompt_message}"
        
        print(f"\n[{self.process_id}] --- Executing Step: '{step.step_name}' ---")
        print(f"[{self.process_id}] Prompt for model: '{prompt}'")

        tools_schema = []
        for tool_name in AVAILABLE_TOOLS.keys():
            tools_schema.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": f"Tool for {tool_name.replace('_', ' ')}",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The task to perform"
                            }
                        },
                        "required": ["prompt"]
                    }
                }
            })

        # Ask model to pick a tool (or answer directly)
        response = await acompletion(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an AI assistant that can use tools to complete tasks. Choose a single best tool if needed; otherwise answer directly."},
                {"role": "user", "content": prompt}
            ],
            tools=tools_schema,
            tool_choice="auto"
        )

        # Extract tool call if present
        try:
            message = response.choices[0].message
        except Exception:
            message = response["choices"][0]["message"]

        tool_calls = getattr(message, "tool_calls", None) or (message.get("tool_calls") if isinstance(message, dict) else None)

        if not tool_calls:
            print(f"[{self.process_id}] Model provided a direct answer.")
            content = getattr(message, "content", None) or (message.get("content") if isinstance(message, dict) else "") or ""
            return AgentOutput(status="completed", result=content)

        tool_call = tool_calls[0]
        fn = getattr(tool_call, "function", None) or tool_call.get("function", {})
        tool_name = (getattr(fn, "name", None) or (fn.get("name") if isinstance(fn, dict) else None)) or ""

        # --- SAME FIX AS YOUR COMMENT ---
        if not tool_name:
            print(f"[{self.process_id}] Error: Model returned a function call with an empty name.")
            return AgentOutput(status="failed", error="Model failed to select a valid tool.")
        # --- END FIX ---

        raw_args = (getattr(fn, "arguments", None) or (fn.get("arguments") if isinstance(fn, dict) else "{}")) or "{}"
        try:
            tool_args = json.loads(raw_args)
        except Exception:
            tool_args = {"prompt": step.prompt_message}

        print(f"[{self.process_id}] 🤔 Model chose to call function: '{tool_name}'")
        print(f"[{self.process_id}]   Arguments: {tool_args}")

        if tool_name in AVAILABLE_TOOLS:
            tool_function = AVAILABLE_TOOLS[tool_name]
            # For mocks, still just pass the prompt. Real tools can use tool_args fully.
            tool_result = tool_function(tool_args.get("prompt", step.prompt_message))
        else:
            print(f"[{self.process_id}] Error: Model tried to call unknown tool '{tool_name}'")
            tool_result = AgentOutput(status="failed", error=f"Unknown tool: {tool_name}")

        print(f"[{self.process_id}] Tool Result: {tool_result}")

        # Send tool result back for a brief model summary (optional)
        # tool_call_id = getattr(tool_call, "id", None) or tool_call.get("id")
        # tool_msg = {
        #     "role": "tool",
        #     "content": json.dumps(tool_result.model_dump()),
        # }
        # if tool_call_id:
        #     tool_msg["tool_call_id"] = tool_call_id

        # final_response = await acompletion(
        #     model=self.model_name,
        #     messages=[
        #         {"role": "system", "content": "Provide a short human-friendly summary of the tool execution result."},
        #         {"role": "user", "content": prompt},
        #         {"role": "assistant", "content": f"I used {tool_name} to complete the task."},
        #         tool_msg,
        #     ]
        # )

        # try:
        #     final_answer = final_response.choices[0].message.content
        # except Exception:
        #     final_answer = final_response["choices"][0]["message"].get("content", "")

        # print(f"[{self.process_id}] Final Answer from model: '{final_answer}'")

        # The final result of the step is the result from the tool itself.
        # The model's final_answer is just a human-friendly summary.
        return tool_result

    async def run(self, plan: list[ProcessStep]):
        print(f"\n[{self.process_id}] ======= STARTING DYNAMIC EXECUTION =======")
        completed_steps = {} # Stores step_id -> result

        i = 0
        while i < len(plan):
            step = plan[i]
            i += 1

            if step.status != "pending": continue

            if not all(dep_id in completed_steps for dep_id in step.dependencies):
                plan.append(step)
                continue

            # --- CONTEXT PASSING ---
            # Create context from the results of dependency steps
            context = ""
            for dep_id in step.dependencies:
                prev_result = completed_steps.get(dep_id)
                if prev_result:
                    context += f"The result of a previous step was: {prev_result.result}\n"
            if not context:
                context = "This is the first step."
            
            step.status = "running"
            result = await self._execute_step(step, context)
            step.output_result = result.model_dump()
            
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
                    for r_step in reversed(recovery_steps):
                        # Make new steps depend on the last successful step before the failure
                        if step.dependencies: r_step.dependencies = [step.dependencies[-1]]
                        plan.insert(i, r_step)
                else:
                    print(f"[{self.process_id}] Planner did not return a recovery plan. Ending execution.")
                    break
            else:
                step.status = "completed"
                self.run_history.append(f"SUCCESS: '{step.step_name}'. Result: {result.result}")
                completed_steps[step.step_id] = result
        
        print(f"[{self.process_id}] ======== EXECUTION FINISHED ========")