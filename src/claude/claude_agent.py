from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions


def create_claude_client() -> ClaudeSDKClient:
    return ClaudeSDKClient(
        options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"]),
    )


async def connect_client(client: ClaudeSDKClient) -> None:
    await client.connect()


async def stream_helpful_claude(client: ClaudeSDKClient, text: str):
    await client.query(prompt=text)
    async for message in client.receive_response():
        yield message
