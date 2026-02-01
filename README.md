# Claude Tutor

A terminal-based programming tutor powered by Claude. Built with Textual and the Claude Agent SDK.

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

## Slash Commands

| Command | Description |
|---------|-------------|
| `/clear` | Clears the conversation history and starts fresh. Your tutor mode setting is preserved. |
| `/tutor` | Toggles tutor mode on/off. When on (default), Claude acts as a teacher. When off, Claude responds normally without the tutoring constraints. |

## Tech Stack

- Python 3.13+
- [Textual](https://textual.textualize.io/) - TUI framework
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk) - Claude integration
- [uv](https://github.com/astral-sh/uv) - Package manager
