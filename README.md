# Claude Tutor

A terminal-based programming tutor powered by Claude. Built with Textual and the Claude Agent SDK.

## Features

- **Tutor Mode** - Claude guides your learning instead of writing code for you
- **Web Search** - Optional online lookup capability
- **MCP Servers** - Extend Claude with external tools via Model Context Protocol
- **Command History** - Navigate previous commands with up/down arrows (persisted across sessions)
- **Query Interruption** - Cancel long-running queries with Escape or Ctrl+C
- **File Access** - Claude can read files in your codebase to provide contextual help

## Overview

Claude Tutor is a TUI (Terminal User Interface) application designed to help you learn programming concepts. Unlike a typical coding assistant, Claude Tutor focuses on teaching rather than writing code for you. It will:

- Explain concepts clearly and thoroughly
- Guide you toward understanding with questions and hints
- Provide small examples to illustrate concepts
- Encourage you to write code yourself
- Review code you share, pointing out what works well and what could be improved

## Installation

```bash
uv sync
```

Or install from PyPI:

```bash
uvx claude_tutor
```

## Running

```bash
uv run python app.py
```

## Using the TUI

When you launch Claude Tutor, you'll see a simple interface with:

- A welcome header at the top
- A chat log area in the middle showing your conversation
- A text input field at the bottom for typing messages

Type your programming questions in the input field and press Enter to send. Claude's responses will appear in the chat log. The interface uses color-coded panels to distinguish between different message types:

- **Blue** - Your messages
- **Red** - Claude's responses
- **Grey** - Tool usage (when Claude reads files in your codebase)
- **Green** - Slash command feedback

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Send message |
| `Up` / `Down` | Navigate command history |
| `Escape` or `Ctrl+C` | Cancel running query |

Command history is automatically saved between sessions.

## Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Shows a list of available commands. |
| `/clear` | Clears the conversation history and starts fresh. Your settings are preserved. |
| `/tutor` | Toggles tutor mode on/off. When on (default), Claude acts as a teacher. When off, Claude responds normally without the tutoring constraints. |
| `/togglewebsearch` | Toggles web search on/off. When on, Claude can use WebSearch and WebFetch tools to look up information online. Disabled by default. |
| `/mcp` | Manage MCP servers. Use `/mcp help` for detailed subcommands. |

## MCP Server Support

Claude Tutor supports [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers, allowing you to extend Claude's capabilities with external tools.

### MCP Commands

| Command | Description |
|---------|-------------|
| `/mcp list` | List all configured servers with connection status |
| `/mcp test [name]` | Test MCP server connections |
| `/mcp add` | Add a new server (interactive wizard) |
| `/mcp add <name> <type> <cmd\|url> [args]` | Add server directly |
| `/mcp remove <name>` | Remove a server |
| `/mcp enable <name>` | Enable a disabled server |
| `/mcp disable <name>` | Disable a server without removing it |
| `/mcp status [name]` | Show server configuration details |

### Server Types

- **stdio** - Local process that communicates via stdin/stdout (e.g., `npx` packages)
- **sse** - Server-Sent Events endpoint
- **http** - HTTP endpoint

### Example: Adding an MCP Server

```
/mcp add filesystem stdio npx -y @anthropic/mcp-filesystem
```

Or use the interactive wizard:
```
/mcp add
```

After adding or modifying servers, use `/clear` to reconnect with the updated configuration.

MCP server configurations are persisted to `~/.local/share/claude-sdk-tutor/mcp_servers.json`.

## Tech Stack

- Python 3.13+
- [Textual](https://textual.textualize.io/) - TUI framework
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk) - Claude integration
- [uv](https://github.com/astral-sh/uv) - Package manager
