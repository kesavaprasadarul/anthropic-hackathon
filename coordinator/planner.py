# /coordinator/planner.py

import os
import json
import re
from typing import List
from pydantic import ValidationError

from database.models import ProcessStep
from dotenv import load_dotenv

# LiteLLM
from litellm import acompletion

load_dotenv()

tool_string = """
**Available Tools:**
- "mock_search_agent": Use this to find and compare options (e.g., highest-rated businesses) and to acquire all necessary contact details at once, such as a website URL, physical address, and phone number. This module cannot make actions, but only read.
- "mock_browser_agent": Use this for a specific action on a known website, like filling out a confirmed online booking form. Do not use this tool to browse or search multiple sites.
- "mock_calendar_agent": Creates events in the user's Google Calendar. Can be used for conxfirmations or to schedule a manual follow-up task for the user as a last resort.
- "mock_calling_agent": Use this to make a phone call to a business when no online booking is available, or if the user specifically requests a call. This can be a primary action if it's the most direct route.
"""

def _strip_md_fences(s: str) -> str:
    if not s:
        return s
    s = s.strip()
    m = re.match(r'^```(?:json)?\s*\r?\n(.*)\r?\n```$', s, flags=re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    first, last = s.find("```"), s.rfind("```")
    if first != -1 and last != -1 and last > first:
        inner = s[first + 3:last]
        inner = re.sub(r'^\s*(?:json)?\s*\r?\n', '', inner, flags=re.IGNORECASE)
        return inner.strip()
    return s

class Planner:
    """
    The brain of the coordinator, responsible for both initial planning
    and dynamic re-planning when failures occur.
    """
    def __init__(self, process_id: str):
        self.process_id = process_id
        # Easily switch models via env; default to Gemini 2.5 Flash Lite
        self.model_name = os.getenv("PLANNER_MODEL", "gemini/gemini-2.5-flash-lite")
        # Supply API key here so you can also point LiteLLM at other providers later.
        self.api_key = (
            os.getenv("GEMINI_KEY")                 # your current setup
            or os.getenv("GEMINI_API_KEY")          # common LiteLLM var
            or os.getenv("GOOGLE_API_KEY")          # fallback if you used this before
        )
        # Common request knobs
        self._req_kwargs = {
            "temperature": 0.2,
            "max_tokens": 8192,
            # Strongly nudge Gemini to give pure JSON
            "extra_body": {"response_mime_type": "application/json"},
            # Pass key explicitly (or rely on env vars if you prefer)
            "api_key": self.api_key,
        }

    def _get_initial_prompt(self, user_prompt: str) -> str:
        return f"""
You are an expert AI task coordinator. Your sole responsibility is to decompose a user's goal into an ideal, optimistic "happy path" sequence of steps. Do not create any fallback plans.

{tool_string}

**Your Task & Rules:**
1.  Create the most direct and efficient `primary` path to achieve the user's goal.
2.  Assume everything will work perfectly.
3.  Use Integer IDs & Dependencies, starting from 1.
4.  Output ONLY a valid JSON array of step objects. NO MARKDOWN, NO CODE FENCES.

**JSON Schema for Each Step Object:**
{{
    "id": "integer", "step_name": "string", "tool_module_name": "string",
    "dependencies": "array of integers", "prompt_message": "string", "path_name": "string (always 'primary')"
}}

---
**User's Goal:** "{user_prompt}"
"""

    def _get_recovery_prompt(self, original_prompt: str, history: List[str], failed_step: ProcessStep) -> str:
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
6.  Output ONLY a valid JSON array of step objects. NO MARKDOWN, NO CODE FENCES.

**JSON Schema for Each Step Object:**
{{
    "id": "integer", "step_name": "string", "tool_module_name": "string",
    "dependencies": "array of integers", "prompt_message": "string", "path_name": "string (always 'recovery')"
}}
"""

    async def generate_initial_plan(self, user_prompt: str) -> List[ProcessStep]:
        prompt = self._get_initial_prompt(user_prompt)
        return await self._generate_plan_from_prompt(prompt)

    async def generate_recovery_plan(self, original_prompt: str, history: List[str], failed_step: ProcessStep) -> List[ProcessStep]:
        prompt = self._get_recovery_prompt(original_prompt, history, failed_step)
        return await self._generate_plan_from_prompt(prompt)

    async def _generate_plan_from_prompt(self, prompt: str) -> List[ProcessStep]:
        """Run the LLM via LiteLLM and map integer IDs -> internal UUIDs."""
        print(f"[{self.process_id}] Generating plan...")
        try:
            resp = await acompletion(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert AI task coordinator. "
                            "Always respond with valid JSON only. NO MARKDOWN, NO CODE FENCES."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                **self._req_kwargs,
            )
        except Exception as e:
            print(f"[{self.process_id}] CRITICAL: LLM call failed. Error: {e}")
            return []

        raw_text = resp.choices[0].message.content
        try:
            raw_json = _strip_md_fences(raw_text)
            plan = json.loads(raw_json)
        except Exception as e:
            print(f"[{self.process_id}] CRITICAL: JSON parse failed. Error: {e}")
            print(f"LLM Output was:\n---\n{raw_text}\n---")
            return []

        try:
            if not isinstance(plan, list):
                raise ValueError("Model did not return a JSON array of steps.")

            id_map = {}
            steps_with_real_ids: List[ProcessStep] = []

            for temp in plan:
                if "id" not in temp:
                    raise ValueError("Each step must include an 'id' field.")
                llm_id = temp.pop("id")
                step = ProcessStep(process_id=self.process_id, **temp)
                id_map[llm_id] = step.step_id
                steps_with_real_ids.append(step)

            # Remap integer deps -> UUID deps
            for step in steps_with_real_ids:
                deps = list(getattr(step, "dependencies", []) or [])
                step.dependencies = [id_map[d] for d in deps if d in id_map]

            print(f"[{self.process_id}] Plan generated and IDs mapped successfully.")
            return steps_with_real_ids

        except Exception as e:
            print(f"[{self.process_id}] CRITICAL: Planning/validation failed. Error: {e}")
            print(f"LLM Output was:\n---\n{raw_text}\n---")
            return []
