import asyncio
from pathlib import Path

from google.antigravity import (
    Agent,
    CapabilitiesConfig,
    LocalOpenAIAgentConfig,
)
from google.antigravity.hooks import policy


PROJECT_DIR = Path(__file__).parent.resolve()


async def main():
    config = LocalOpenAIAgentConfig(
        model="gemma4:26b",
        base_url="http://localhost:11434/v1",
        workspaces=[str(PROJECT_DIR)],
        capabilities=CapabilitiesConfig(),
        policies=[policy.allow_all()],
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

    async with Agent(config=config) as agent:
        response = await agent.chat(prompt)
        print(await response.text())


if __name__ == "__main__":
    asyncio.run(main())