from textual.binding import Binding
from textual.widgets import Input

from claude.history import CommandHistory


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
