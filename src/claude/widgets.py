from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Input, Static

from claude.history import CommandHistory


class StatusBar(Static):
    """Reactive status bar showing tutor/web/mcp states."""

    tutor_on: reactive[bool] = reactive(True)
    web_on: reactive[bool] = reactive(False)
    mcp_count: reactive[int] = reactive(0)

    def render(self) -> str:
        tutor = "on" if self.tutor_on else "off"
        web = "on" if self.web_on else "off"
        mcp = f"{self.mcp_count} server{'s' if self.mcp_count != 1 else ''}"
        return f"tutor: {tutor}  ·  web: {web}  ·  mcp: {mcp}"


class ASCIISpinner(Static):
    """Minimal spinner that cycles through frames with a label."""

    SPINNER_FRAMES = ["·  ", "·· ", "···", " ··", "  ·", "   "]

    _frame: reactive[int] = reactive(0)
    _label: reactive[str] = reactive("")
    _running: reactive[bool] = reactive(False)

    def __init__(self, label: str = "Processing...", **kwargs):
        super().__init__(**kwargs)
        self._label = label
        self._timer = None

    def render(self) -> str:
        if not self._running:
            return ""
        frame = self.SPINNER_FRAMES[self._frame % len(self.SPINNER_FRAMES)]
        return f"{frame} {self._label}"

    def start(self, label: str = "Processing query...") -> None:
        """Start the spinner animation."""
        self._label = label
        self._running = True
        self._frame = 0
        self.display = True
        if self._timer is None:
            self._timer = self.set_interval(0.1, self._advance_frame)

    def stop(self) -> None:
        """Stop the spinner animation."""
        self._running = False
        self.display = False
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def _advance_frame(self) -> None:
        """Advance to the next spinner frame."""
        if self._running:
            self._frame = (self._frame + 1) % len(self.SPINNER_FRAMES)


class HistoryInput(Input):
    """Input widget with command history navigation."""

    BINDINGS = [
        Binding("up", "history_previous", "Previous command", show=False),
        Binding("down", "history_next", "Next command", show=False),
        Binding("escape", "app.cancel_query", "Cancel", show=False),
        Binding("ctrl+c", "app.cancel_query", "Cancel", show=False),
    ]

    def __init__(self, history: CommandHistory, **kwargs):
        super().__init__(**kwargs)
        self.history = history

    def action_history_previous(self) -> None:
        """Navigate to previous command in history."""
        self.value = self.history.navigate_up(self.value)
        self.cursor_position = len(self.value)

    def action_history_next(self) -> None:
        """Navigate to next command in history."""
        self.value = self.history.navigate_down(self.value)
        self.cursor_position = len(self.value)
