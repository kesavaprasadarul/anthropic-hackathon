# /coordinator/executor.py

import os, json, asyncio
from typing import List, Dict, Any

from smolagents import Tool, CodeAgent
from smolagents.models import LiteLLMModel

from agents.MOCKS import (
    mock_search_agent, mock_browser_agent, mock_calendar_agent, mock_calling_agent, AgentOutput
)
from database.models import ProcessStep
from .planner import Planner

SYSTEM_PROMPT = "You are an execution agent. Call the available function exactly once with JSON args. Return the tool result only; do not add commentary."

# --- Thin Tool wrappers for smolagents (one arg: prompt) ---

class _BaseMockTool(Tool):
    inputs = {"prompt": {"type": "string", "description": "Instruction for the tool."}}
    output_type = "string"  # return JSON string of AgentOutput

    def _call_sync(self, coro):
        # Run async mock tools safely whether we're in an event loop or not
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        else:
            # If already in a loop, run in a separate task and wait
            return loop.run_until_complete(coro)  # works if called from non-async context inside agent

    def _return_json(self, ao: AgentOutput) -> str:
        return json.dumps(ao.model_dump(), ensure_ascii=False)

class SearchTool(_BaseMockTool):
    name = "mock_search_agent"
    description = "Find & compare options and return website/phone/address."
    def forward(self, prompt: str) -> str:
        return self._return_json(self._call_sync(mock_search_agent(prompt)))

class BrowserTool(_BaseMockTool):
    name = "mock_browser_agent"
    description = "Perform a specific action on a known website (e.g., submit booking form)."
    def forward(self, prompt: str) -> str:
        return self._return_json(self._call_sync(mock_browser_agent(prompt)))

class CalendarTool(_BaseMockTool):
    name = "mock_calendar_agent"
    description = "Create or modify Google Calendar events."
    def forward(self, prompt: str) -> str:
        return self._return_json(self._call_sync(mock_calendar_agent(prompt)))

class CallingTool(_BaseMockTool):
    name = "mock_calling_agent"
    description = "Place a phone call to the business to book."
    def forward(self, prompt: str) -> str:
        return self._return_json(self._call_sync(mock_calling_agent(prompt)))

TOOLS_BY_NAME: Dict[str, Tool] = {
    "mock_search_agent": SearchTool(),
    "mock_browser_agent": BrowserTool(),
    "mock_calendar_agent": CalendarTool(),
    "mock_calling_agent": CallingTool(),
}

class Executor:
    def __init__(self, process_id: str, original_prompt: str, run_history: List[str]):
        self.process_id = process_id
        self.original_prompt = original_prompt
        self.run_history = run_history
        self.model = LiteLLMModel(
            model_id=os.getenv("EXECUTOR_MODEL", "gemini/gemini-2.5-flash-lite"),
            api_key=(os.getenv("GEMINI_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        )

    def _make_agent_for_step(self, tool_name: str) -> CodeAgent:
        tool = TOOLS_BY_NAME.get(tool_name)
        if not tool:
            # Build a “no-op” agent that will immediately return an error
            class NoopTool(Tool):
                name = "noop"
                description = "Unknown tool."
                inputs = {"prompt": {"type": "string"}}
                output_type = "string"
                def forward(self, prompt: str) -> str:
                    return json.dumps({"status":"failed","error":f"Unknown tool: {tool_name}"})
            tool = NoopTool()
        # Agent only sees the single tool we want it to call
        return CodeAgent(
            tools=[tool],
            model=self.model,
        )

    async def _execute_step(self, step: ProcessStep, context: str) -> AgentOutput:
        print(f"\n[{self.process_id}] --- Executing Step: '{step.step_name}' ---")
        user_prompt = SYSTEM_PROMPT + f" Context from previous steps:\n{context}\n\nYour task now:\n{step.prompt_message}"
        print(f"[{self.process_id}] Prompt for model: '{user_prompt}'")

        agent = self._make_agent_for_step(step.tool_module_name)
        # smolagents handles tool-calling loop internally
        tool_result_str = agent.run(task=user_prompt)

        # Tools return AgentOutput as JSON string; parse it back
        try:
            payload = json.loads(tool_result_str)
            ao = AgentOutput(**payload)
        except Exception:
            # If a tool returned plain text, wrap it
            ao = AgentOutput(status="completed", result=tool_result_str)

        print(f"[{self.process_id}] Tool Result: status='{ao.status}' result={ao.result!r} error={ao.error}")
        return ao

    async def run(self, plan: List[ProcessStep]):
        print(f"\n[{self.process_id}] ======= STARTING DYNAMIC EXECUTION =======")
        completed_steps: Dict[str, AgentOutput] = {}
        i = 0
        while i < len(plan):
            step = plan[i]; i += 1
            if step.status != "pending":
                continue
            if not all(dep_id in completed_steps for dep_id in step.dependencies):
                plan.append(step); continue

            # Build context
            ctx = "\n".join(
                f"The result of a previous step was: {completed_steps[d].result}"
                for d in step.dependencies if d in completed_steps
            ) or "This is the first step."

            step.status = "running"
            result = await self._execute_step(step, ctx)
            step.output_result = result.model_dump()

            if result.status == "failed":
                step.status = "failed"
                self.run_history.append(f"ATTEMPTED: '{step.step_name}' but it FAILED with error: {result.error}")
                print(f"[{self.process_id}] Step '{step.step_name}' failed. Triggering re-planning...")
                planner = Planner(self.process_id)
                recovery_steps = await planner.generate_recovery_plan(self.original_prompt, self.run_history, step)
                if recovery_steps:
                    print(f"[{self.process_id}] Received {len(recovery_steps)} recovery steps. Splicing into plan.")
                    for r in reversed(recovery_steps):
                        if step.dependencies:
                            r.dependencies = [step.dependencies[-1]]
                        plan.insert(i, r)
                else:
                    print(f"[{self.process_id}] Planner did not return a recovery plan. Ending execution.")
                    break
            else:
                step.status = "completed"
                self.run_history.append(f"SUCCESS: '{step.step_name}'. Result: {result.result}")
                completed_steps[step.step_id] = result

        print(f"[{self.process_id}] ======== EXECUTION FINISHED ========")
