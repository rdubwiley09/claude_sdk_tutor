import json

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    query,
)
from rich.markdown import Markdown as RichMarkdown
from rich.panel import Panel
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, Footer, Input, RichLog, LoadingIndicator

from claude.claude_agent import (
    connect_client,
    create_claude_client,
    stream_helpful_claude,
)
from claude.history import CommandHistory
from claude.mcp_commands import McpAsyncCommand, McpCommandHandler
from claude.mcp_config import McpConfigManager
from claude.widgets import HistoryInput


class MyApp(App):
    def __init__(self):
        super().__init__()
        self.tutor_mode = True
        self.web_search_enabled = False
        self.mcp_config = McpConfigManager()
        self.mcp_handler = McpCommandHandler(self.mcp_config)
        self.mcp_add_state: dict | None = None  # For interactive /mcp add wizard
        self.client = self._create_client()
        self.history = CommandHistory()

    def _create_client(self):
        """Create a new Claude client with current settings."""
        return create_claude_client(
            tutor_mode=self.tutor_mode,
            web_search=self.web_search_enabled,
            mcp_servers=self.mcp_config.get_enabled_servers_for_sdk(),
        )

    CSS = """
    #main {
        height: 100%;
    }
    Input {
        height: auto;
        margin-top: 1;
        margin-left: 3;
        margin-right: 3;
        margin-bottom: 1;
    }
    #header {
        content-align: center middle;
        width: 100%;
        margin-top: 1;
        margin-bottom: 1;
        height: auto;
    }
    RichLog {
        background: $boost;
        margin-left: 3;
        margin-right: 3;
        height: 1fr;
    }
    LoadingIndicator {
        height: auto;
        margin-left: 3;
        margin-right: 3;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="main"):
            yield Static("Welcome to claude SDK tutor!", id="header")
            yield RichLog(markup=True, highlight=True)
            yield LoadingIndicator(id="spinner")
            yield HistoryInput(history=self.history)
        yield Footer()

    async def on_mount(self) -> None:
        self.query_one("#spinner", LoadingIndicator).display = False
        await connect_client(self.client)

    def write_user_message(self, message: str) -> None:
        log = self.query_one(RichLog)
        log.write(Panel(RichMarkdown(message), title="You", border_style="dodger_blue1"))

    def write_system_message(self, message: str) -> None:
        log = self.query_one(RichLog)
        log.write(Panel(RichMarkdown(message), title="Claude", border_style="red"))

    def write_tool_message(self, name: str, input: dict) -> None:
        log = self.query_one(RichLog)
        input_str = json.dumps(input, indent=2)
        content = f"**{name}**\n```json\n{input_str}\n```"
        log.write(Panel(RichMarkdown(content), title="Tool", border_style="grey50"))

    def write_slash_message(self, message: str) -> None:
        log = self.query_one(RichLog)
        log.write(Panel(RichMarkdown(message), title="Slash", border_style="green"))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        self.query_one(HistoryInput).value = ""
        if command:
            self.history.add(command)

        # Handle interactive MCP add wizard
        if self.mcp_add_state is not None:
            if command.lower() == "/cancel":
                self.mcp_add_state = None
                self.write_slash_message("Cancelled MCP server setup.")
                return
            self._handle_mcp_add_step(command)
            return

        if command == "/clear":
            self.run_worker(self.clear_conversation())
            return
        if command == "/tutor":
            self.run_worker(self.toggle_tutor_mode())
            return
        if command == "/togglewebsearch":
            self.run_worker(self.toggle_web_search())
            return
        if command == "/help":
            self.show_help()
            return
        if command.lower().startswith("/mcp"):
            self._handle_mcp_command(command)
            return
        self.write_user_message(event.value)
        self.query_one("#spinner", LoadingIndicator).display = True
        self.run_worker(self.get_response(event.value))

    async def clear_conversation(self) -> None:
        self.query_one(RichLog).clear()
        self.client = self._create_client()
        await connect_client(self.client)
        self.write_slash_message("Context cleared")

    async def toggle_tutor_mode(self) -> None:
        self.tutor_mode = not self.tutor_mode
        self.query_one(RichLog).clear()
        self.client = self._create_client()
        await connect_client(self.client)
        status = "on" if self.tutor_mode else "off"
        self.write_slash_message(f"Tutor mode {status}")

    async def toggle_web_search(self) -> None:
        self.web_search_enabled = not self.web_search_enabled
        self.query_one(RichLog).clear()
        self.client = self._create_client()
        await connect_client(self.client)
        status = "on" if self.web_search_enabled else "off"
        self.write_slash_message(f"Web search {status}")

    def show_help(self) -> None:
        help_text = """**Available Commands**

- `/help` - Show this help message
- `/clear` - Clear conversation history and start fresh
- `/tutor` - Toggle tutor mode on/off (guides learning vs gives code)
- `/togglewebsearch` - Toggle web search on/off (allows online lookups)
- `/mcp` - Manage MCP servers (use `/mcp help` for details)"""
        self.write_slash_message(help_text)

    def _handle_mcp_command(self, command: str) -> None:
        """Handle /mcp commands."""
        result = self.mcp_handler.handle_command(command)
        if result is None:
            # Start interactive add wizard
            self.mcp_add_state = {"step": 0, "name": "", "type": "", "data": {}}
            self.write_slash_message(
                "**Add MCP Server**\n\nEnter server name (or `/cancel` to abort):"
            )
        elif isinstance(result, McpAsyncCommand):
            # Async command needs connection testing
            self.query_one("#spinner", LoadingIndicator).display = True
            self.run_worker(self._test_mcp_connections(result))
        else:
            self.write_slash_message(result)

    async def _test_mcp_connections(self, cmd: McpAsyncCommand) -> None:
        """Test MCP server connections and display results."""
        try:
            mcp_servers = self.mcp_config.get_enabled_servers_for_sdk()
            if not mcp_servers:
                if cmd.command == "test":
                    self.write_slash_message(
                        "**MCP Test**\n\nNo enabled servers to test."
                    )
                else:
                    self.write_slash_message(
                        self.mcp_handler.handle_list(cmd.args, connection_status=None)
                    )
                return

            # Build allowed tools for the test
            allowed_tools = [f"mcp__{name}__*" for name in mcp_servers]

            options = ClaudeAgentOptions(
                mcp_servers=mcp_servers,
                allowed_tools=allowed_tools,
                max_turns=1,
            )

            connection_status: dict[str, str] = {}

            # Run a minimal query just to get the init message with MCP status
            async for message in query(prompt="test", options=options):
                if isinstance(message, SystemMessage) and message.subtype == "init":
                    mcp_info = message.data.get("mcp_servers", [])
                    for server in mcp_info:
                        name = server.get("name", "unknown")
                        status = server.get("status", "unknown")
                        connection_status[name] = status
                    break

            # Display results based on command
            if cmd.command == "test":
                self.write_slash_message(
                    self.mcp_handler.handle_test(cmd.args, connection_status)
                )
            else:  # list
                self.write_slash_message(
                    self.mcp_handler.handle_list(cmd.args, connection_status)
                )
        except Exception as e:
            self.write_slash_message(f"**Error** testing MCP connections: {e}")
        finally:
            self.query_one("#spinner", LoadingIndicator).display = False

    def _handle_mcp_add_step(self, user_input: str) -> None:
        """Handle a step in the interactive MCP add wizard."""
        state = self.mcp_add_state
        if state is None:
            return

        step = state["step"]

        if step == 0:
            # Got server name
            name = user_input.strip()
            if not name:
                self.write_slash_message("**Error**: Name cannot be empty. Try again:")
                return
            if self.mcp_config.get_server(name):
                self.write_slash_message(
                    f"**Error**: Server `{name}` already exists. Enter a different name:"
                )
                return
            state["name"] = name
            state["step"] = 1
            self.write_slash_message(
                "Select server type:\n- `stdio` - Local process\n- `sse` - Server-Sent Events\n- `http` - HTTP endpoint"
            )

        elif step == 1:
            # Got server type
            server_type = user_input.strip().lower()
            if server_type not in ("stdio", "sse", "http"):
                self.write_slash_message(
                    f"**Error**: Invalid type `{server_type}`. Enter `stdio`, `sse`, or `http`:"
                )
                return
            state["type"] = server_type
            state["step"] = 2
            if server_type == "stdio":
                self.write_slash_message("Enter command to run (e.g., `npx`):")
            else:
                self.write_slash_message("Enter server URL:")

        elif step == 2:
            # Got command or URL
            value = user_input.strip()
            if not value:
                self.write_slash_message("**Error**: Value cannot be empty. Try again:")
                return

            if state["type"] == "stdio":
                state["data"]["command"] = value
                state["step"] = 3
                self.write_slash_message(
                    "Enter arguments (space-separated, or leave empty):"
                )
            else:
                # SSE or HTTP - URL provided, we're done
                config = {"type": state["type"], "url": value}
                self.mcp_config.add_server(state["name"], config)
                self.write_slash_message(
                    f"**Added** server `{state['name']}` ({state['type']})\n\n"
                    "Use `/clear` to reconnect with new MCP servers."
                )
                self.mcp_add_state = None

        elif step == 3:
            # Got args for stdio command
            args = user_input.strip().split() if user_input.strip() else []
            config = {
                "type": "stdio",
                "command": state["data"]["command"],
                "args": args,
            }
            self.mcp_config.add_server(state["name"], config)
            self.write_slash_message(
                f"**Added** server `{state['name']}` (stdio)\n\n"
                "Use `/clear` to reconnect with new MCP servers."
            )
            self.mcp_add_state = None

    async def get_response(self, text: str) -> None:
        try:
            async for message in stream_helpful_claude(self.client, text):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if hasattr(block, "text"):
                            self.write_system_message(block.text)
                        elif hasattr(block, "name"):
                            self.write_tool_message(
                                block.name, getattr(block, "input", {})
                            )
                elif isinstance(message, ResultMessage):
                    pass  # Might want to add logging later
        finally:
            self.query_one("#spinner", LoadingIndicator).display = False


def main():
    app = MyApp()
    app.run()


if __name__ == "__main__":
    main()
