# Claude SDK Tutor

A terminal-based chat interface for learning programming with Claude. Built with Textual and the Claude Agent SDK, it provides an interactive TUI where Claude acts as a programming tutor rather than simply writing code for you.

## Features

- **Tutor Mode**: Claude guides learning through explanations and hints instead of providing complete solutions
- **Web Search**: Optional web lookup capability (toggle with `/togglewebsearch`)
- **MCP Servers**: Connect external tools via Model Context Protocol (stdio, SSE, HTTP transports)
- **Command History**: Navigate previous commands with up/down arrows (persisted across sessions)
- **Query Interruption**: Cancel running queries with Escape or Ctrl+C

## Setup

```bash
uv sync
```

## Run

```bash
uv run python app.py
```

## Slash Commands

- `/help` - Show available commands
- `/clear` - Clear conversation and reconnect
- `/tutor` - Toggle tutor mode on/off
- `/togglewebsearch` - Toggle web search capability
- `/mcp` - Manage MCP servers (use `/mcp help` for subcommands)

## Architecture

```
app.py              # Main Textual app with UI and command handling
src/claude/
  claude_agent.py   # Claude SDK client creation and streaming
  widgets.py        # Custom HistoryInput widget with keybindings
  history.py        # Persistent command history
  mcp_config.py     # MCP server configuration storage
  mcp_commands.py   # /mcp command parsing and handlers
```

## Tech Stack

- Python 3.13+
- Textual (TUI framework)
- Claude Agent SDK
- uv (package manager)
