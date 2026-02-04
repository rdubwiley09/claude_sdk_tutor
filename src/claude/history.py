from pathlib import Path

from platformdirs import user_data_dir


class CommandHistory:
    """Manages command history with persistence to disk."""

    MAX_ENTRIES = 1000

    def __init__(self):
        self.history: list[str] = []
        self.index: int = -1
        self.temp_input: str = ""
        self._history_file = Path(user_data_dir("claude-sdk-tutor")) / "command_history.txt"
        self._load()

    def _load(self) -> None:
        """Load history from disk."""
        if self._history_file.exists():
            try:
                lines = self._history_file.read_text().splitlines()
                self.history = lines[-self.MAX_ENTRIES :]
            except OSError:
                self.history = []

    def _save(self) -> None:
        """Save history to disk."""
        try:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            self._history_file.write_text("\n".join(self.history[-self.MAX_ENTRIES :]))
        except OSError:
            pass

    def add(self, command: str) -> None:
        """Add a command to history, skipping consecutive duplicates."""
        command = command.strip()
        if not command:
            return
        if not self.history or self.history[-1] != command:
            self.history.append(command)
            self._save()
        self.reset_navigation()

    def reset_navigation(self) -> None:
        """Reset navigation state."""
        self.index = -1
        self.temp_input = ""

    def navigate_up(self, current_input: str) -> str:
        """Navigate to previous command in history."""
        if not self.history:
            return current_input

        if self.index == -1:
            self.temp_input = current_input
            self.index = len(self.history) - 1
        elif self.index > 0:
            self.index -= 1

        return self.history[self.index]

    def navigate_down(self, current_input: str) -> str:
        """Navigate to next command in history, or restore original input."""
        if self.index == -1:
            return current_input

        if self.index < len(self.history) - 1:
            self.index += 1
            return self.history[self.index]
        else:
            self.index = -1
            return self.temp_input
