# /coordinator/executor.py

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Awaitable

from litellm import acompletion  # async, provider-agnostic chat API

from agents.MOCKS import mock_browser_agent, mock_calling_agent, AgentOutput
import agents.web_search.booking_agent as booking_agent
import agents.web_search.search_agent as search_agent
from database.models import ProcessStep
from .planner import Planner

# Make sure the phone-calls agent helpers are importable despite the dash in the folder name.
PHONE_CALLS_DIR = Path(__file__).resolve().parent.parent / "agents" / "phone-calls"
if PHONE_CALLS_DIR.exists():
    phone_calls_path = str(PHONE_CALLS_DIR)
    if phone_calls_path not in sys.path:
        sys.path.append(phone_calls_path)

try:
    from calling_agent import CallingModuleAgent  # type: ignore
except Exception as import_error:  # pragma: no cover - defensive fallback
    CallingModuleAgent = None  # type: ignore
    CALLING_AGENT_IMPORT_ERROR = import_error
else:
    CALLING_AGENT_IMPORT_ERROR = None

try:
    from calling_module.input_adapter import InputAdapter  # type: ignore
except Exception:  # pragma: no cover - defensive fallback
    InputAdapter = None  # type: ignore
    _CALLING_PAYLOAD_NORMALIZER = None
else:
    _CALLING_PAYLOAD_NORMALIZER = InputAdapter()

BOOKING_AGENT = booking_agent.BookingAgent()
SEARCH_AGENT = search_agent.PlaceSearchAgent()

CALLING_MODULE_BASE_URL = os.getenv("CALLING_MODULE_URL", "http://localhost:8001")
CALLING_AGENT_INSTANCE = None
CALLING_AGENT_INIT_ERROR: Optional[Exception] = None

if 'CallingModuleAgent' in locals() and CallingModuleAgent is not None:  # type: ignore
    try:
        CALLING_AGENT_INSTANCE = CallingModuleAgent(base_url=CALLING_MODULE_BASE_URL)
    except Exception as exc:  # pragma: no cover - defensive fallback
        CALLING_AGENT_INIT_ERROR = exc
else:
    CALLING_AGENT_INIT_ERROR = CALLING_AGENT_IMPORT_ERROR


def _prompt_only_schema(tool_name: str, description: str) -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Natural language instructions for the tool.",
                    }
                },
                "required": ["prompt"],
            },
        },
    }


def _normalize_agent_output(value: Any) -> AgentOutput:
    if isinstance(value, AgentOutput):
        return value
    if isinstance(value, dict):
        try:
            return AgentOutput(**value)
        except Exception:
            return AgentOutput(status="completed", result=json.dumps(value, ensure_ascii=False))
    if value is None:
        return AgentOutput(status="completed", result="")
    return AgentOutput(status="completed", result=str(value))


def _sync_prompt_invoker(func: Callable[[str], Any], label: str) -> Callable[[Dict[str, Any], str], Awaitable[AgentOutput]]:
    async def _invoke(args: Dict[str, Any], default_prompt: str) -> AgentOutput:
        prompt_value = args.get("prompt", default_prompt)
        try:
            result = func(prompt_value)
        except Exception as exc:
            return AgentOutput(status="failed", error=f"{label} failed: {exc}")
        return _normalize_agent_output(result)

    return _invoke


def _async_prompt_invoker(func: Callable[[str], Any], label: str) -> Callable[[Dict[str, Any], str], Awaitable[AgentOutput]]:
    async def _invoke(args: Dict[str, Any], default_prompt: str) -> AgentOutput:
        prompt_value = args.get("prompt", default_prompt)
        try:
            result = await func(prompt_value)  # type: ignore[arg-type]
        except Exception as exc:
            return AgentOutput(status="failed", error=f"{label} failed: {exc}")
        return _normalize_agent_output(result)

    return _invoke

def _normalize_call_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict) or _CALLING_PAYLOAD_NORMALIZER is None:
        return payload

    adapter = _CALLING_PAYLOAD_NORMALIZER

    # Top-level required fields
    for field in ("business", "user", "intent"):
        if field not in payload:
            raise ValueError(f"Calling agent payload is missing '{field}'.")

    intent = str(payload.get("intent", "")).lower().strip()
    if intent not in {"reserve", "reschedule", "cancel", "info"}:
        raise ValueError(
            "Calling agent payload 'intent' must be one of: reserve, reschedule, cancel, info."
        )

    business = payload.get("business")
    if isinstance(business, dict):
        phone_raw = business.get("phone")
        if phone_raw is not None:
            normalized = adapter._normalize_phone(str(phone_raw))
            if not adapter._is_valid_phone(normalized):
                raise ValueError(
                    "business.phone must be a valid E.164 phone number (e.g., +1234567890)."
                )
            business["phone"] = normalized
        if not business.get("name"):
            raise ValueError("Calling agent payload business.name is required.")

    user = payload.get("user")
    if isinstance(user, dict):
        callback = user.get("callback_phone")
        if callback:
            normalized_callback = adapter._normalize_phone(str(callback))
            if adapter._is_valid_phone(normalized_callback):
                user["callback_phone"] = normalized_callback
        if not user.get("name"):
            raise ValueError("Calling agent payload user.name is required.")

    if intent == "reserve":
        reservation = payload.get("reservation")
        if not isinstance(reservation, dict):
            raise ValueError(
                "Reservation intent requires a 'reservation' object (see README example)."
            )

        missing_fields = [key for key in ("date", "party_size", "time_window") if not reservation.get(key)]
        if missing_fields:
            raise ValueError(
                "Reservation payload is missing required fields: " + ", ".join(missing_fields)
            )

        time_window = reservation.get("time_window")
        if not isinstance(time_window, dict):
            raise ValueError("Reservation time_window must be an object with start_time and end_time.")

        if not time_window.get("start_time") or not time_window.get("end_time"):
            raise ValueError("Reservation time_window requires both start_time and end_time (HH:MM).")

        # Ensure party size is positive int
        try:
            party_size = int(reservation["party_size"])
        except (ValueError, TypeError):
            raise ValueError("Reservation party_size must be an integer.") from None
        if party_size < 1:
            raise ValueError("Reservation party_size must be at least 1.")
        reservation["party_size"] = party_size

    elif intent == "reschedule":
        if "reschedule" not in payload:
            raise ValueError("Reschedule intent requires a 'reschedule' object.")

    elif intent == "cancel":
        if "cancel" not in payload:
            raise ValueError("Cancel intent requires a 'cancel' object.")

    elif intent == "info":
        if "info" not in payload:
            raise ValueError("Info intent requires an 'info' object.")

    return payload


async def _invoke_calling_agent(args: Dict[str, Any], default_prompt: str) -> AgentOutput:
    payload_raw = args.get("task_payload")
    if payload_raw is None:
        payload_raw = args.get("prompt", default_prompt)

    if isinstance(payload_raw, dict):
        task_payload = payload_raw
    else:
        payload_text = str(payload_raw).strip()
        try:
            task_payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            message = "Calling agent expects 'task_payload' to be a JSON object string describing the call request."
            return AgentOutput(status="failed", error=f"{message} JSON error: {exc}")
        if not isinstance(task_payload, dict):
            return AgentOutput(status="failed", error="Calling agent payload must be a JSON object.")

    try:
        task_payload = _normalize_call_payload(task_payload)
    except ValueError as exc:
        return AgentOutput(status="failed", error=f"Calling agent payload error: {exc}")

    if CALLING_AGENT_INSTANCE is None:
        fallback_reason = (
            f"Real calling agent unavailable ({CALLING_AGENT_INIT_ERROR})" if CALLING_AGENT_INIT_ERROR else "Real calling agent unavailable"
        )
        print(f"[Executor] {fallback_reason}. Falling back to mock calling agent.")
        return await mock_calling_agent(args.get("prompt", default_prompt))

    try:
        response_dict = await asyncio.to_thread(CALLING_AGENT_INSTANCE.start_call, task_payload)
    except Exception as exc:
        return AgentOutput(status="failed", error=f"Calling Module error: {exc}")

    response_text = json.dumps(response_dict, ensure_ascii=False)
    return AgentOutput(status="completed", result=response_text)

CALLING_AGENT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "mock_calling_agent",
        "description": (
            "Initiate a real phone call via the Calling Module service. Provide the exact JSON. If the phone number is not in E.164 format, assume Germany and format it accordingly. "
            "payload you would POST to `/start_call` under the `task_payload` field."
            "The payload that you need to pass looks like this: {\"business\":{\"phone\":\"+4915117831779\",\"name\":\"Bella Vista Restaurant\",\"timezone\":\"America/New_York\"},\"user\":{\"name\":\"Maria Schmidt\",\"callback_phone\":\"+15005550006\"},\"intent\":\"reserve\",\"reservation\":{\"date\":\"2024-01-20\",\"time_window\":{\"start_time\":\"19:00\",\"end_time\":\"21:00\"},\"party_size\":2,\"notes\":\"Anniversary dinner for our 5th wedding anniversary\",\"budget_range\":\"€60–100 per person\"},\"locale\":\"en-US\",\"policy\":{\"autonomy_level\":\"medium\",\"max_call_duration_minutes\":4}}"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task_payload": {
                    "type": "object",
                    "description": (
                        "Structured call request payload mirroring the `/start_call` schema. Must include `business`, "
                        "`user`, and `intent` keys."
                    ),
                    "required": ["business", "user", "intent"],
                    "properties": {
                        "business": {
                            "type": "object",
                            "required": ["phone", "name"],
                            "properties": {
                                "phone": {"type": "string", "description": "Business phone number in E.164 format."},
                                "name": {"type": "string", "description": "Business display name."},
                                "timezone": {"type": "string"},
                                "website": {"type": "string"},
                                "address": {"type": "string"},
                            },
                        },
                        "user": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"type": "string", "description": "User's name shared with the business."},
                                "callback_phone": {"type": "string"},
                                "email": {"type": "string"},
                            },
                        },
                        "intent": {
                            "type": "string",
                            "enum": ["reserve", "reschedule", "cancel", "info"],
                        },
                        "reservation": {"type": "object"},
                        "reschedule": {"type": "object"},
                        "cancel": {"type": "object"},
                        "info": {"type": "object"},
                        "policy": {"type": "object"},
                        "locale": {"type": "string"},
                        "task_id": {"type": ["string", "null"]},
                    },
                },
                "prompt": {
                    "type": "string",
                    "description": (
            "Initiate a real phone call via the Calling Module service. Provide the exact JSON. If the phone number is not in E.164 format, assume Germany and format it accordingly. "
            "payload you would POST to `/start_call` under the `task_payload` field."
            "The payload that you need to pass looks like this: {\"business\":{\"phone\":\"+4915117831779\",\"name\":\"Bella Vista Restaurant\",\"timezone\":\"America/New_York\"},\"user\":{\"name\":\"Maria Schmidt\",\"callback_phone\":\"+15005550006\"},\"intent\":\"reserve\",\"reservation\":{\"date\":\"2024-01-20\",\"time_window\":{\"start_time\":\"19:00\",\"end_time\":\"21:00\"},\"party_size\":2,\"notes\":\"Anniversary dinner for our 5th wedding anniversary\",\"budget_range\":\"€60–100 per person\"},\"locale\":\"en-US\",\"policy\":{\"autonomy_level\":\"medium\",\"max_call_duration_minutes\":4}}"
            ),
                },
            },
            "required": ["task_payload"],
        },
    },
}


AVAILABLE_TOOLS: Dict[str, Dict[str, Any]] = {
    "mock_search_agent": {
        "schema": _prompt_only_schema(
            "mock_search_agent",
            "Search for businesses and reservation options using Google Places.",
        ),
        "invoke": _sync_prompt_invoker(SEARCH_AGENT.search, "Search agent"),
    },
    "mock_browser_agent": {
        "schema": _prompt_only_schema(
            "mock_browser_agent",
            "Simulate browser automation for web forms (mock).",
        ),
        "invoke": _async_prompt_invoker(mock_browser_agent, "Browser agent"),
    },
    "mock_booking_agent": {
        "schema": _prompt_only_schema(
            "mock_booking_agent",
            "Create appointments or reservations via the calendar agent.",
        ),
        "invoke": _sync_prompt_invoker(BOOKING_AGENT.create_appointment, "Booking agent"),
    },
    "mock_availability_agent": {
        "schema": _prompt_only_schema(
            "mock_availability_agent",
            "Check availability via the calendar agent.",
        ),
        "invoke": _sync_prompt_invoker(BOOKING_AGENT.check_availability, "Availability agent"),
    },
    "mock_calling_agent": {
        "schema": CALLING_AGENT_SCHEMA,
        "invoke": _invoke_calling_agent,
    },
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

        tools_schema = [tool_info["schema"] for tool_info in AVAILABLE_TOOLS.values()]

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

        tool_entry = AVAILABLE_TOOLS.get(tool_name)
        if tool_entry is None:
            print(f"[{self.process_id}] Error: Model tried to call unknown tool '{tool_name}'")
            tool_result = AgentOutput(status="failed", error=f"Unknown tool: {tool_name}")
        else:
            tool_invoker = tool_entry["invoke"]
            tool_result = await tool_invoker(tool_args, step.prompt_message)

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