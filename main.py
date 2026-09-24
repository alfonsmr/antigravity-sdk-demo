import asyncio
import json
import platform
import subprocess
import sys
import time
import urllib.request

from importlib.metadata import version
from pathlib import Path

from google.antigravity import (
    Agent,
    CapabilitiesConfig,
    LocalOpenAIAgentConfig,
)
from google.antigravity import types
from google.antigravity.hooks import hooks, policy


MODEL = "gemma4:26b"
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_OPENAI_URL = f"{OLLAMA_HOST}/v1"

PROJECT_DIR = Path(__file__).parent.resolve()

tool_call_count = 0


def separator(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def bytes_to_gb(value: int | None) -> str:
    if value is None:
        return "unknown"
    return f"{value / (1024 ** 3):.2f} GB"


def ollama_get(path: str) -> dict:
    with urllib.request.urlopen(f"{OLLAMA_HOST}{path}") as response:
        return json.load(response)


def ollama_post(path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        f"{OLLAMA_HOST}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        return json.load(response)


def print_environment() -> None:
    separator("DEMO ENVIRONMENT")

    print(f"Python:              {sys.version.split()[0]}")
    print(f"Operating system:    {platform.system()} {platform.release()}")
    print(f"Architecture:        {platform.machine()}")
    print(f"Antigravity SDK:     {version('google-antigravity')}")
    print(f"Workspace:           {PROJECT_DIR}")


def print_ollama_info() -> None:
    separator("OLLAMA SERVER")

    try:
        server = ollama_get("/api/version")

        print(f"Ollama server:       ONLINE")
        print(f"Ollama version:      {server.get('version', 'unknown')}")
        print(f"Server address:      {OLLAMA_HOST}")
        print(f"OpenAI endpoint:     {OLLAMA_OPENAI_URL}")
        print("Network location:    localhost")
        print("Remote model API:    NO")
    except Exception as error:
        print(f"Ollama server:       ERROR")
        print(f"Reason:              {error}")
        raise


def print_model_info() -> None:
    separator("LOCAL MODEL")

    print(f"Requested model:     {MODEL}")

    try:
        model = ollama_post(
            "/api/show",
            {"model": MODEL},
        )

        details = model.get("details", {})

        print(f"Model family:        {details.get('family', 'unknown')}")
        print(f"Parameter size:      {details.get('parameter_size', 'unknown')}")
        print(
            f"Quantization:        "
            f"{details.get('quantization_level', 'unknown')}"
        )

    except Exception as error:
        print(f"Model metadata:      unavailable ({error})")


def print_loaded_models(label: str) -> None:
    separator(label)

    try:
        data = ollama_get("/api/ps")
        models = data.get("models", [])

        if not models:
            print("No models currently loaded in Ollama memory.")
            return

        for model in models:
            print(f"Model:               {model.get('name')}")
            print(f"Memory footprint:    {bytes_to_gb(model.get('size_vram'))}")
            print(f"Context length:      {model.get('context_length', 'unknown')}")
            print(f"Expires at:          {model.get('expires_at', 'unknown')}")
            print()

    except Exception as error:
        print(f"Unable to query Ollama process state: {error}")


def run_tests(label: str) -> None:
    separator(label)

    result = subprocess.run(
        ["uv", "run", "python", "-m", "unittest", "-v"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr

    print(output.strip())
    print()
    print(f"Exit code:           {result.returncode}")


def print_git_status(label: str) -> None:
    separator(label)

    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )

    if result.stdout.strip():
        print(result.stdout.strip())
    else:
        print("Working tree clean.")


@hooks.pre_tool_call_decide
async def before_tool(data: types.ToolCall) -> types.HookResult:
    global tool_call_count
    tool_call_count += 1

    print()
    print(f"[AGENT TOOL #{tool_call_count}]")
    print(f"Tool: {data.name}")

    if data.args:
        formatted_args = json.dumps(
            data.args,
            indent=2,
            default=str,
        )
        print("Arguments:")
        print(formatted_args)

    return types.HookResult(allow=True)


@hooks.post_tool_call
async def after_tool(data) -> None:
    print(f"[TOOL COMPLETE] {data.name}")

    if getattr(data, "error", None):
        print(f"Error: {data.error}")


def print_usage(usage, title: str) -> None:
    separator(title)

    if usage is None:
        print("Token usage was not reported by the model backend.")
        return

    print(
        f"Prompt tokens:       "
        f"{usage.prompt_token_count if usage.prompt_token_count is not None else 'n/a'}"
    )
    print(
        f"Output tokens:       "
        f"{usage.candidates_token_count if usage.candidates_token_count is not None else 'n/a'}"
    )
    print(
        f"Thinking tokens:     "
        f"{usage.thoughts_token_count if usage.thoughts_token_count is not None else 'n/a'}"
    )
    print(
        f"Cached tokens:       "
        f"{usage.cached_content_token_count if usage.cached_content_token_count is not None else 'n/a'}"
    )
    print(
        f"Total tokens:        "
        f"{usage.total_token_count if usage.total_token_count is not None else 'n/a'}"
    )


async def main():
    print_environment()
    print_ollama_info()
    print_model_info()

    print_loaded_models("OLLAMA STATE BEFORE AGENT")

    run_tests("TESTS BEFORE ANTIGRAVITY")
    print_git_status("GIT STATUS BEFORE ANTIGRAVITY")

    separator("ANTIGRAVITY CONFIGURATION")

    print(f"Model:               {MODEL}")
    print(f"Provider:            Ollama")
    print(f"Protocol:            OpenAI-compatible API")
    print(f"Endpoint:            {OLLAMA_OPENAI_URL}")
    print(f"Workspace:           {PROJECT_DIR}")
    print(f"Agent mode:          autonomous / lightweight")
    print(f"External cloud LLM:  NO")

    config = LocalOpenAIAgentConfig(
        model=MODEL,
        base_url=OLLAMA_OPENAI_URL,
        workspaces=[str(PROJECT_DIR)],
        capabilities=CapabilitiesConfig(),
        policies=[policy.allow_all()],
        hooks=[
            before_tool,
            after_tool,
        ],
    ).lightweight()

    prompt = """
Inspect the Python project in the active workspace.

Run the test suite using:

    uv run python -m unittest -v

Some tests are failing.

Find the problem and fix the implementation until all tests pass.

Rules:
- Do not modify test_calculator.py.
- Do not modify main.py.
- Only change the implementation that needs fixing.
- Do not use Git or modify Git history.
- Run the tests again after making changes.
- Do not stop until all tests pass.

When finished, briefly explain what you changed and report the final test result.
"""

    separator("STARTING ANTIGRAVITY AGENT")

    print("Sending task to Antigravity SDK...")
    print(f"Local model:         {MODEL}")
    print(f"Ollama endpoint:     {OLLAMA_OPENAI_URL}")

    start_time = time.perf_counter()

    async with Agent(config=config) as agent:
        response = await agent.chat(prompt)

        separator("AGENT FINAL RESPONSE")
        print(await response.text())

        elapsed = time.perf_counter() - start_time

        print_usage(
            response.usage_metadata,
            "ANTIGRAVITY TURN TOKEN USAGE",
        )

        print_usage(
            agent.conversation.total_usage,
            "ANTIGRAVITY SESSION TOKEN USAGE",
        )

    separator("EXECUTION SUMMARY")

    print(f"Model:               {MODEL}")
    print(f"Provider:            Ollama")
    print(f"Execution location:  localhost")
    print(f"Tool calls:          {tool_call_count}")
    print(f"Total elapsed time:  {elapsed:.2f} seconds")

    print_loaded_models("OLLAMA STATE AFTER AGENT")

    run_tests("INDEPENDENT TEST VERIFICATION")
    print_git_status("FILES CHANGED BY AGENT")


if __name__ == "__main__":
    asyncio.run(main())