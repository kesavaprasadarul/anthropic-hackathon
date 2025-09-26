"""Smolagents integration for the Calling Module service.

This module exposes a smolagents-compatible tool and lightweight agent wrapper
that can initiate outbound phone calls by invoking the Calling Module FastAPI
service via HTTP.  It is designed so other agents can simply invoke a single
tool (`start_phone_call`) with the full JSON payload they would normally send to
`/start_call`.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional, Union

import requests
from smolagents import CodeAgent, Tool
from smolagents.models import LiteLLMModel

DEFAULT_BASE_URL = os.getenv("CALLING_MODULE_URL", "http://localhost:8001")
DEFAULT_MODEL_ID = (
    os.getenv("CALLING_AGENT_MODEL")
    or os.getenv("MODEL_NAME")
    or "anthropic/claude-3-haiku-20240307"
)
DEFAULT_API_KEY = os.getenv("CALLING_AGENT_API_KEY") or os.getenv("GOOGLE_API_KEY")
DEFAULT_TIMEOUT = int(os.getenv("CALLING_AGENT_TIMEOUT_SECONDS", "600"))

_FENCE_RE = re.compile(r"^```(?:json)?\s*\r?\n(.*)\r?\n```$", re.IGNORECASE | re.DOTALL)


def _strip_fences(text: str) -> str:
    """Remove Markdown code fences if present."""

    match = _FENCE_RE.match(text.strip())
    return match.group(1).strip() if match else text.strip()


def _coerce_to_dict(obj: Any) -> Dict[str, Any]:
    """Best-effort conversion of an agent response to a JSON dictionary."""

    if isinstance(obj, dict):
        return obj

    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:  # pragma: no cover - defensive
            pass

    if isinstance(obj, (bytes, bytearray)):
        obj = obj.decode("utf-8", "replace")

    if isinstance(obj, str):
        candidate = _strip_fences(obj)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return {"status": "completed", "result": candidate}

    try:
        return json.loads(json.dumps(obj))
    except Exception:  # pragma: no cover - defensive
        return {"status": "completed", "result": str(obj)}


class StartPhoneCallTool(Tool):
    """Smolagents tool that bridges to the Calling Module `/start_call` endpoint."""

    name = "start_phone_call"
    description = (
        "Initiate an outbound phone call via the Calling Module API and return the "
        "normalized post-call result. Provide the exact JSON payload that `/start_call` "
        "expects (business, user, intent, etc.)."
    )
    inputs = {
        "task_payload": {
            "type": "string",
            "description": (
                "JSON string describing the call task (business, user, intent, etc.). "
                "This will be forwarded directly to the Calling Module `/start_call` endpoint."
            ),
        },
        "timeout_seconds": {
            "type": "integer",
            "description": (
                "Optional override for the HTTP request timeout in seconds. Defaults to the "
                "CALLING_AGENT_TIMEOUT_SECONDS environment variable or 600 seconds."
            ),
            "optional": True,
            "nullable": True,
        },
    }
    output_type = "object"

    def __init__(self, base_url: Optional[str] = None, default_timeout: Optional[int] = None) -> None:
        super().__init__(
            name=self.name,
            description=self.description,
            inputs=self.inputs,
            output_type=self.output_type,
        )
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.default_timeout = default_timeout or DEFAULT_TIMEOUT

    def _post(self, payload: Dict[str, Any], timeout_seconds: Optional[int]) -> Dict[str, Any]:
        url = f"{self.base_url}/start_call"
        timeout = timeout_seconds or self.default_timeout

        try:
            response = requests.post(url, json=payload, timeout=timeout)
        except requests.Timeout:
            return {
                "status": "timeout",
                "error": f"Calling Module timed out after {timeout} seconds",
            }
        except requests.RequestException as exc:  # pragma: no cover - network errors
            return {
                "status": "failed",
                "error": f"Calling Module request failed: {exc}",
            }

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            return {
                "status": "failed",
                "error": f"Calling Module returned {response.status_code}: {detail}",
                "exception": str(exc),
            }

        try:
            return response.json()
        except ValueError:
            return {
                "status": "failed",
                "error": "Calling Module returned a non-JSON response",
                "raw_response": response.text,
            }

    def forward(self, task_payload: Union[str, Dict[str, Any]], timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        if isinstance(task_payload, dict):
            payload = task_payload
        else:
            try:
                payload = json.loads(task_payload)
            except json.JSONDecodeError as exc:
                return {
                    "status": "failed",
                    "error": f"Invalid JSON provided to task_payload: {exc}",
                }

        return self._post(payload, timeout_seconds)


class CallingModuleAgent:
    """Lightweight convenience wrapper that constructs a `CodeAgent` for phone calls."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        model: Optional[Any] = None,
        model_id: Optional[str] = None,
        api_key: Optional[str] = None,
        default_timeout: Optional[int] = None,
        use_llm: Optional[bool] = None,
    ) -> None:
        self.base_url = base_url or DEFAULT_BASE_URL
        self.tool = StartPhoneCallTool(self.base_url, default_timeout)
        self._agent: Optional[CodeAgent] = None

        if use_llm is None:
            use_llm = model is not None or model_id is not None or api_key is not None

        self._use_llm = use_llm

        if self._use_llm:
            if model is None:
                model_id = model_id or DEFAULT_MODEL_ID
                api_key = api_key or DEFAULT_API_KEY
                if not api_key:
                    raise ValueError(
                        "Missing API key for CallingModuleAgent. Set CALLING_AGENT_API_KEY, "
                        "GOOGLE_API_KEY, or pass `api_key=` explicitly."
                    )

                model = LiteLLMModel(
                    model_id=model_id,
                    api_key=api_key,
                    model_kwargs={"response_mime_type": "application/json"},
                )

            self._agent = CodeAgent(
                tools=[self.tool],
                model=model,
                additional_authorized_imports=["json"],
            )

    _REQUIRED_FIELDS = ("business", "user", "intent")

    @classmethod
    def _validate_task_payload(cls, task: Dict[str, Any]) -> None:
        missing = []
        for field in cls._REQUIRED_FIELDS:
            if field not in task:
                missing.append(field)
                continue

            value = task[field]
            if value is None:
                missing.append(field)
            elif isinstance(value, str) and not value.strip():
                missing.append(field)
            elif isinstance(value, dict) and not value:
                missing.append(field)

        if missing:
            raise ValueError(
                "CallingModuleAgent task payload is missing required fields: " + ", ".join(sorted(set(missing)))
            )

    def start_call(self, task: Dict[str, Any], *, timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Ask the agent to initiate a phone call with the provided task payload."""
        if not isinstance(task, dict):
            raise ValueError("CallingModuleAgent.start_call expects a dictionary payload.")

        if not self._use_llm or self._agent is None:
            return self.start_call_via_tool(task, timeout_seconds=timeout_seconds)

        self._validate_task_payload(task)

        payload_json = json.dumps(task, ensure_ascii=False)
        timeout_fragment = (
            f" Override the timeout to {timeout_seconds} seconds by passing timeout_seconds to the tool call." if timeout_seconds else ""
        )

        instruction = f"""
        You are orchestrating the Jarvis Calling Module. Use the provided tool `start_phone_call` exactly once
        with the JSON payload provided below without modifying keys or values.{timeout_fragment}

        Payload:
        ```json
        {payload_json}
        ```

        After invoking the tool, return ONLY the JSON response from the tool without additional commentary.
        """

        raw = self._agent.run(task=instruction.strip())
        return _coerce_to_dict(raw)

    def start_call_via_tool(self, task: Union[Dict[str, Any], str], *, timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Bypass the LLM and call the tool directly."""
        if isinstance(task, str):
            try:
                task_payload = json.loads(task)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON task payload provided to CallingModuleAgent: {exc}") from exc
        else:
            task_payload = task

        if not isinstance(task_payload, dict):
            raise ValueError("CallingModuleAgent task payload must be a JSON object.")

        self._validate_task_payload(task_payload)

        payload_json = json.dumps(task_payload, ensure_ascii=False)
        return self.tool.forward(payload_json, timeout_seconds)


__all__ = [
    "StartPhoneCallTool",
    "CallingModuleAgent",
]
