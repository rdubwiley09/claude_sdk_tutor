from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Vertical, Horizontal
from textual.widgets import Static, Footer, Input, Markdown

from src.claude_agent import stream_helpful_claude


def get_user_message(message: str) -> str:
    return f"""
## User Message:
### {message}
"""


def get_system_message(message: str) -> str:
    return f"""
## System Message:
### {message}
"""


class RightAligned(Horizontal):
    DEFAULT_CSS = """
    RightAligned{
        align: right top;
    }
    """


class UserMessageBubble(Markdown):
    def __init__(self, message: str) -> None:
        super().__init__(get_user_message(message))


class SystemMessageBubble(Markdown):
    def __init__(self, message: str) -> None:
        super().__init__(get_system_message(message))


class MyApp(App):
    CSS = """
    Input {
        margin-top: 1;
        margin-left: 3;
        margin-right: 3;
        margin-bottom: 1;
    }
    #header {
        content-align: center middle;
        width: 100%;
        margin-top: 1;
    }
    VerticalScroll {
        background: $boost;
        margin-left: 3;
        margin-right: 3;
    }
    UserMessageBubble {
        width: 80%;
        content-align: left top;
        padding-left: 1;
        margin-left: 3;
        border: heavy green;
    }
    SystemMessageBubble {
        width: 80%;
        align: right top;
        padding-left: 1;
        margin-left: 3;
        border: heavy blue; 
    }    
    """

    def compose(self) -> ComposeResult:
        yield Static("Welcome to the helper!", id="header")
        yield VerticalScroll()
        yield Input()
        yield Footer()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.query_one(Input).value = ""
        self.query_one(VerticalScroll).mount(UserMessageBubble(event.value))
        self.query_one(VerticalScroll).mount(
            RightAlignted(SystemMessageBubble("Thinking...", id="loading"))
        )
        self.run_worker(self.get_response(event.value))
        self.query_one(VerticalScroll).scroll_end(animate=True)

    async def get_response(self, text: str) -> None:
        self.query_one("#loading").remove()
        messages = await run_helpful_claude(text)
        for message in messages:
            self.query_one(VerticalScroll).mount(
                RightAligned(SystemMessageBubble(message))
            )


if __name__ == "__main__":
    app = MyApp()
    app.run()
