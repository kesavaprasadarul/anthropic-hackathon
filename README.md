# Butler AI Coordinator

This repository contains the Butler coordinator built for the Anthropic hackathon. Butler is a FastAPI service that plans, routes, and supervises a collection of automation agents that can search the web, browse booking sites, place phone calls, and record follow-up tasks for the user.

The coordinator accepts a natural-language goal from a user, breaks it into an optimistic multi-step plan with a large language model, executes each step through specialized agent modules, and keeps track of progress for UI clients. The system ships with mocks for demoability and can be wired up to real browser, search, and calling modules when the required credentials are available.

## Key Capabilities
- Multi-step planning through `coordinator/planner.py` using LiteLLM-compatible models.
- Asynchronous execution engine (`coordinator/executor.py`) that dispatches to web search, browser automation, phone, and calendar agents.
- FastAPI surface (`main.py`) with `/execute-task` and `/status/{process_id}` endpoints plus in-memory state for hackathon demos.
- Modular agents in `agents/` with rich sub-systems for browser automation, web search, and phone calling.
- Pydantic models in `database/models.py` that expose plan snapshots in a UI-friendly shape.

## Repository Layout
- `main.py` – FastAPI entrypoint that exposes the coordinator as an HTTP service.
- `coordinator/` – Planner and executor logic, including recovery planning.
- `agents/` – Agent implementations and mocks (`browser_agent/`, `web_search/`, `phone-calls/`, etc.).
- `database/models.py` – Pydantic data contracts for plan state and UI serialization.
- `coordinator.md` – Original product notes describing the desired coordinator behaviour.
- `requirements.txt` / `req.txt` – Python dependency sets (lightweight vs. full stack).

## Getting Started
### Prerequisites
- Python 3.11+ is recommended.
- Access tokens for the model and optional agent integrations (Anthropic, Google, ElevenLabs, Twilio, etc.).

### Installation
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
# For the full agent stack (browser automation, calling module, etc.) use:
# pip install -r req.txt
```

### Environment configuration
Create a `.env` file or export variables before running the coordinator. Common variables include:
- `MODEL_NAME` / `PLANNER_MODEL_NAME` – LiteLLM model identifiers (e.g. `anthropic/claude-3-haiku-20240307`).
- Provider API keys used by LiteLLM (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.).
- `GOOGLE_API_KEY`, `GOOGLE_MAPS_KEY` – Required by the web search agent.
- `CALLING_MODULE_URL`, `CALLING_AGENT_API_KEY` – Base URL and auth for the phone-calls microservice.
- `ELEVENLABS_*`, `TWILIO_*` – Optional voice calling integrations inside `agents/phone-calls/`.

The service loads environment variables via `python-dotenv`, so any values in `.env` at the project root will be picked up automatically.

### Running the API
```bash
uvicorn main:app --reload
```
Send work to the coordinator:
```bash
curl -X POST http://localhost:8000/execute-task \
  -H 'Content-Type: application/json' \
  -d '{"user_id": "demo-user", "prompt": "Book dinner for two tomorrow at an Italian restaurant in Munich."}'
```
Track progress:
```bash
curl http://localhost:8000/status/<process_id>
```
Responses contain the current status and the latest task breakout derived from `database.models.PlanTask`.

## Development Notes
- Tests (where available) can be run with `pytest`.
- The coordinator currently stores process state in memory (`HACKATHON_DB`, `PROCESS_RUNS`, `PROCESS_STATUS`). Swap these stores for a persistent database before production use.
- The mock agents in `agents/MOCKS.py` allow running the end-to-end flow without external services. Replace them with the real modules when deploying.
- Browser automation relies on the `browser-use` framework; see `agents/browser_agent/README.md` for details and integration guidance.

## Background & Next Steps
`coordinator.md` captures the original product vision: derive optimistic plans, layer recovery flows, and deepen the user knowledge base over time. The current implementation focuses on planning and executing primary/recovery flows with LiteLLM-backed reasoning. Future work typically includes:
- Persisting plans and run history in a real database.
- Building a knowledge base of previously resolved user tasks.
- Hardening integrations with real browser, calling, and calendar providers.

Feel free to adapt this scaffolding to new domains by adding tools in `agents/` and extending the planner prompt instructions.
