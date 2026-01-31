import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssitantMessage, ResultMessage


async def stream_helpful_claude(text: str):
    async for message in query(
        prompt=text, options=ClaudeAgentOptions(allowed_tools=["Read", "WebSearch"])
    ):
        yield message
