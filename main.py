import asyncio

from google.antigravity import Agent, LocalOpenAIAgentConfig


async def main():
    config = LocalOpenAIAgentConfig(
        model="gemma4:26b",
        base_url="http://localhost:11434/v1",
    ).lightweight()

    async with Agent(config) as agent:
        response = await agent.chat(
            "Say hello and tell me which model you are."
        )

        async for token in response:
            print(token, end="", flush=True)

        print()


if __name__ == "__main__":
    asyncio.run(main())