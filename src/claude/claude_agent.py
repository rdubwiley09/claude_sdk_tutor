from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

TUTOR_SYSTEM_PROMPT = """You are a programming tutor. Your role is to help users learn and understand code, not to write code for them.

When a user asks a question:
- Explain concepts clearly and thoroughly
- Guide them toward understanding with questions and hints
- If they're stuck, provide small examples to illustrate concepts
- Encourage them to write the code themselves
- Review and explain code they show you, pointing out what works well and what could be improved

Never write complete solutions for them. Instead, help them develop the skills to solve problems independently."""


def create_claude_client(
    tutor_mode: bool = True,
    web_search: bool = False,
    mcp_servers: dict | None = None,
) -> ClaudeSDKClient:
    tools = ["Read", "Glob", "Grep"]
    if web_search:
        tools.extend(["WebSearch", "WebFetch"])
    if mcp_servers:
        # Allow all tools from each configured MCP server
        for server_name in mcp_servers:
            tools.append(f"mcp__{server_name}__*")
    options = ClaudeAgentOptions(allowed_tools=tools, mcp_servers=mcp_servers or {})
    if tutor_mode:
        options.system_prompt = TUTOR_SYSTEM_PROMPT
    return ClaudeSDKClient(options=options)


async def connect_client(client: ClaudeSDKClient) -> None:
    await client.connect()


async def stream_helpful_claude(client: ClaudeSDKClient, text: str):
    await client.query(prompt=text)
    async for message in client.receive_response():
        yield message
