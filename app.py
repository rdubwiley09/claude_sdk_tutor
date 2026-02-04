import json

from claude_agent_sdk import AssistantMessage, ResultMessage
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
from claude.widgets import HistoryInput


class MyApp(App):
    def __init__(self):
        super().__init__()
        self.tutor_mode = True
        self.web_search_enabled = False
        self.client = create_claude_client(
            tutor_mode=self.tutor_mode, web_search=self.web_search_enabled
        )
        self.history = CommandHistory()

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
        self.write_user_message(event.value)
        self.query_one("#spinner", LoadingIndicator).display = True
        self.run_worker(self.get_response(event.value))

    async def clear_conversation(self) -> None:
        self.query_one(RichLog).clear()
        self.client = create_claude_client(
            tutor_mode=self.tutor_mode, web_search=self.web_search_enabled
        )
        await connect_client(self.client)
        self.write_slash_message("Context cleared")

    async def toggle_tutor_mode(self) -> None:
        self.tutor_mode = not self.tutor_mode
        self.query_one(RichLog).clear()
        self.client = create_claude_client(
            tutor_mode=self.tutor_mode, web_search=self.web_search_enabled
        )
        await connect_client(self.client)
        status = "on" if self.tutor_mode else "off"
        self.write_slash_message(f"Tutor mode {status}")

    async def toggle_web_search(self) -> None:
        self.web_search_enabled = not self.web_search_enabled
        self.query_one(RichLog).clear()
        self.client = create_claude_client(
            tutor_mode=self.tutor_mode, web_search=self.web_search_enabled
        )
        await connect_client(self.client)
        status = "on" if self.web_search_enabled else "off"
        self.write_slash_message(f"Web search {status}")

    def show_help(self) -> None:
        help_text = """**Available Commands**

- `/help` - Show this help message
- `/clear` - Clear conversation history and start fresh
- `/tutor` - Toggle tutor mode on/off (guides learning vs gives code)
- `/togglewebsearch` - Toggle web search on/off (allows online lookups)"""
        self.write_slash_message(help_text)

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
