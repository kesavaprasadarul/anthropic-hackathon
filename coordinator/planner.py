# /coordinator/planner.py

import os
import json
import uuid
from typing import List
from pydantic import ValidationError

from litellm import acompletion  # <-- replace genai with LiteLLM

from database.models import ProcessStep
from dotenv import load_dotenv

load_dotenv()
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))  # <-- removed

tool_string = """
**Available Tools:**
- "mock_search_agent": Use this to find and compare options (e.g., highest-rated businesses) and to acquire all necessary contact details at once, such as a website URL, physical address, and phone number. This module cannot make actions, but only read.
- "mock_browser_agent": Use this for a specific action on a known website, like filling out a confirmed online booking form. Do not use this tool to browse or search multiple sites.
- "mock_calendar_agent": Creates events in the user's Google Calendar. Can be used for confirmations or to schedule a manual follow-up task for the user as a last resort.
- "mock_calling_agent": Use this to make a phone call to a business when no online booking is available, or if the user specifically requests a call. This can be a primary action if it's the most direct route.
"""

class Planner:
    """
    The brain of the coordinator, responsible for both initial planning
    and dynamic re-planning when failures occur.
    """
    def __init__(self, process_id: str):
        self.process_id = process_id

        # Minimal replacement for generation config
        self.model_name = os.getenv("PLANNER_MODEL_NAME", os.getenv("MODEL_NAME", "gemini/gemini-2.5-flash-lite"))
        self.gen_kwargs = {
            "temperature": 0.2,
            "top_p": 1,
            # "top_k" is provider-specific; omitted for portability
            "max_tokens": 8192,  # maps to OpenAI-style; some providers may ignore/rename
            "response_mime_type": "application/json",
        }
        # Prefer JSON output when supported (OpenAI-compatible). Safe to keep; ignored by others.
        self.response_format = {"type": "json_object"}

    def _get_initial_prompt(self, user_prompt: str) -> str:
        """Generates the prompt for creating the initial, optimistic plan."""
        return f"""
You are an expert AI task coordinator. Your sole responsibility is to decompose a user's goal into an ideal, optimistic "happy path" sequence of steps. Do not create any fallback plans.

{tool_string}

**Your Task & Rules:**
1.  Create the most direct and efficient `primary` path to achieve the user's goal.
2.  Assume everything will work perfectly.
3.  Use Integer IDs & Dependencies, starting from 1.
4.  Output ONLY a valid JSON array of step objects.

**JSON Schema for Each Step Object:**
{{
    "id": "integer", "step_name": "string", "tool_module_name": "string",
    "dependencies": "array of integers", "prompt_message": "string", "path_name": "string (always 'primary')"
}}

---
**User's Goal:** "{user_prompt}"
"""

    def _get_recovery_prompt(self, original_prompt: str, history: List[str], failed_step: ProcessStep) -> str:
        """Generates a specialized prompt to create a recovery plan after a failure."""
        history_str = "\n".join(f"- {item}" for item in history)
        return f"""
You are an expert AI problem-solving coordinator. A multi-step plan has failed. Your task is to create a short, new sequence of "recovery" steps to overcome the failure.

**Original User Goal:** "{original_prompt}"

**Execution History (What has happened so far):**
{history_str}

**Failed Step Details:**
- Step Name: "{failed_step.step_name}"
- Tool Used: "{failed_step.tool_module_name}"
- Action Attempted: "{failed_step.prompt_message}"
- Error Result: "{failed_step.output_result.get('error', 'No error message.')}"

{tool_string}

**Your Task & Rules:**
1.  Analyze the failure and the history.
2.  Propose a new plan to achieve the original goal via the next best method. (e.g., if `web_browser` failed, the next best method is `calling`).
3.  **This new plan must be complete.** If the original goal included a final confirmation step (like adding to a calendar), you MUST include that step in this recovery plan, making it dependent on your new recovery actions.
4.  The `path_name` for all new steps must be 'recovery'.
5.  Use Integer IDs & Dependencies, starting from 1.
6.  Output ONLY a valid JSON array of step objects.

**JSON Schema for Each Step Object:**
{{
    "id": "integer", "step_name": "string", "tool_module_name": "string",
    "dependencies": "array of integers", "prompt_message": "string", "path_name": "string (always 'recovery')"
}}
"""

    async def generate_initial_plan(self, user_prompt: str) -> List[ProcessStep]:
        """Public method to create the first plan."""
        prompt = self._get_initial_prompt(user_prompt)
        return await self._generate_plan_from_prompt(prompt)

    async def generate_recovery_plan(self, original_prompt: str, history: List[str], failed_step: ProcessStep) -> List[ProcessStep]:
        """Public method to create a recovery plan."""
        print("in recovery")
        prompt = self._get_recovery_prompt(original_prompt, history, failed_step)
        return await self._generate_plan_from_prompt(prompt)

    async def _generate_plan_from_prompt(self, prompt: str) -> List[ProcessStep]:
        """Helper function to run the LLM call and map IDs, used by both public methods."""
        print(f"[{self.process_id}] Generating plan...")
        try:
            # Replace genai.generate_content_async with LiteLLM completion
            resp = await acompletion(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a planner that outputs ONLY JSON arrays conforming to the requested schema."},
                    {"role": "user", "content": prompt},
                ],
                response_format=self.response_format,  # best-effort JSON mode
                **self.gen_kwargs,
            )

            try:
                content = resp.choices[0].message.content
            except Exception:
                content = resp["choices"][0]["message"]["content"]

            raw_plan_data = json.loads(content)

            id_map = {}
            steps_with_real_ids = []

            for temp_step_data in raw_plan_data:
                llm_id = temp_step_data.pop('id')
                step = ProcessStep(process_id=self.process_id, **temp_step_data)
                id_map[llm_id] = step.step_id
                steps_with_real_ids.append(step)

            for step in steps_with_real_ids:
                integer_deps = step.dependencies
                uuid_deps = []
                for dep_id in integer_deps:
                    if dep_id in id_map:
                        uuid_deps.append(id_map[dep_id])
                step.dependencies = uuid_deps

            print(f"[{self.process_id}] Plan generated and IDs mapped successfully.")
            return steps_with_real_ids

        except Exception as e:
            print(f"[{self.process_id}] CRITICAL: Failed during planning or validation. Error: {e}")
            if 'content' in locals():
                print(f"LLM Output was:\n---\n{content}\n---")
            return []
