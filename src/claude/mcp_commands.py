"""MCP command handling for slash commands."""

from dataclasses import dataclass

from .mcp_config import McpConfigManager, McpServerEntry


@dataclass
class McpAsyncCommand:
    """Indicates an async command that needs special handling."""

    command: str
    args: list[str]


class McpCommandHandler:
    """Handles /mcp slash commands."""

    def __init__(self, config_manager: McpConfigManager):
        self.config = config_manager

    def parse_command(self, command: str) -> tuple[str, list[str]]:
        """Parse /mcp command into subcommand and args.

        Example: "/mcp add myserver" -> ("add", ["myserver"])
        """
        parts = command.strip().split()
        # Remove /mcp prefix if present
        if parts and parts[0].lower() == "/mcp":
            parts = parts[1:]

        if not parts:
            return "help", []

        subcommand = parts[0].lower()
        args = parts[1:]
        return subcommand, args

    def handle_command(self, command: str) -> str | None | McpAsyncCommand:
        """Handle a /mcp command.

        Returns:
            str: Markdown response to display
            None: Trigger interactive mode
            McpAsyncCommand: Command needs async handling
        """
        subcommand, args = self.parse_command(command)

        # Commands that need async handling (connection testing)
        if subcommand in ("test", "list"):
            return McpAsyncCommand(command=subcommand, args=args)

        handlers = {
            "add": self.handle_add,
            "remove": self.handle_remove,
            "enable": self.handle_enable,
            "disable": self.handle_disable,
            "status": self.handle_status,
            "help": self.handle_help,
        }

        handler = handlers.get(subcommand, self.handle_help)
        return handler(args)

    def handle_list(
        self, _args: list[str], connection_status: dict[str, str] | None = None
    ) -> str:
        """List all configured MCP servers with optional connection status."""
        servers = self.config.list_servers()

        if not servers:
            return "**MCP Servers**\n\nNo servers configured. Use `/mcp add` to add one."

        lines = ["**MCP Servers**\n"]
        lines.append("| Name | Type | Enabled | Connection | Target |")
        lines.append("|------|------|---------|------------|--------|")

        for server in servers:
            server_type = server.config.get("type", "stdio")
            enabled = "yes" if server.enabled else "no"
            target = self._get_target_display(server)

            if connection_status and server.name in connection_status:
                conn = connection_status[server.name]
            elif not server.enabled:
                conn = "—"
            else:
                conn = "unknown"

            lines.append(
                f"| {server.name} | {server_type} | {enabled} | {conn} | {target} |"
            )

        return "\n".join(lines)

    def handle_test(
        self, args: list[str], connection_status: dict[str, str]
    ) -> str:
        """Format test results for MCP server connections."""
        if not connection_status:
            return "**MCP Test**\n\nNo enabled servers to test."

        # Filter to specific server if provided
        if args:
            name = args[0]
            if name not in connection_status:
                server = self.config.get_server(name)
                if not server:
                    return f"**Error**: Server `{name}` not found."
                if not server.enabled:
                    return f"**Error**: Server `{name}` is disabled."
                return f"**Error**: Server `{name}` was not tested."
            connection_status = {name: connection_status[name]}

        lines = ["**MCP Connection Test**\n"]

        connected = 0
        failed = 0
        for name, status in connection_status.items():
            if status == "connected":
                lines.append(f"- `{name}`: **connected**")
                connected += 1
            else:
                lines.append(f"- `{name}`: **{status}**")
                failed += 1

        lines.append(f"\n**Summary**: {connected} connected, {failed} failed")
        return "\n".join(lines)

    def _get_target_display(self, server: McpServerEntry) -> str:
        """Get display string for server target."""
        config = server.config
        server_type = config.get("type", "")

        if server_type == "stdio":
            cmd = config.get("command", "")
            args = config.get("args", [])
            if args:
                return f"{cmd} {' '.join(args[:2])}{'...' if len(args) > 2 else ''}"
            return cmd
        elif server_type in ("sse", "http"):
            return config.get("url", "")
        return "—"

    def handle_add(self, args: list[str]) -> str | None:
        """Handle /mcp add command.

        If args provided: /mcp add <name> <type> <command/url> [args...]
        If no args: return None to trigger interactive mode
        """
        if not args:
            return None  # Trigger interactive mode

        if len(args) < 3:
            return "**Error**: Usage: `/mcp add <name> <type> <command|url> [args...]`"

        name = args[0]
        server_type = args[1].lower()

        if server_type not in ("stdio", "sse", "http"):
            return f"**Error**: Invalid type `{server_type}`. Must be stdio, sse, or http."

        if self.config.get_server(name):
            return f"**Error**: Server `{name}` already exists."

        if server_type == "stdio":
            command = args[2]
            cmd_args = args[3:] if len(args) > 3 else []
            config = {"type": "stdio", "command": command, "args": cmd_args}
        else:
            url = args[2]
            config = {"type": server_type, "url": url}

        self.config.add_server(name, config)
        return f"**Added** server `{name}` ({server_type})"

    def handle_remove(self, args: list[str]) -> str:
        """Handle /mcp remove <name> command."""
        if not args:
            return "**Error**: Usage: `/mcp remove <name>`"

        name = args[0]
        if self.config.remove_server(name):
            return f"**Removed** server `{name}`"
        return f"**Error**: Server `{name}` not found."

    def handle_enable(self, args: list[str]) -> str:
        """Handle /mcp enable <name> command."""
        if not args:
            return "**Error**: Usage: `/mcp enable <name>`"

        name = args[0]
        if self.config.enable_server(name):
            return f"**Enabled** server `{name}`"
        return f"**Error**: Server `{name}` not found."

    def handle_disable(self, args: list[str]) -> str:
        """Handle /mcp disable <name> command."""
        if not args:
            return "**Error**: Usage: `/mcp disable <name>`"

        name = args[0]
        if self.config.disable_server(name):
            return f"**Disabled** server `{name}`"
        return f"**Error**: Server `{name}` not found."

    def handle_status(self, args: list[str]) -> str:
        """Handle /mcp status [name] command."""
        if not args:
            # Show summary status
            servers = self.config.list_servers()
            enabled = sum(1 for s in servers if s.enabled)
            return f"**MCP Status**: {enabled}/{len(servers)} servers enabled"

        name = args[0]
        server = self.config.get_server(name)
        if not server:
            return f"**Error**: Server `{name}` not found."

        lines = [f"**Server: {name}**\n"]
        lines.append(f"- **Type**: {server.config.get('type', 'unknown')}")
        lines.append(f"- **Status**: {'enabled' if server.enabled else 'disabled'}")

        server_type = server.config.get("type", "")
        if server_type == "stdio":
            cmd = server.config.get("command", "")
            args_list = server.config.get("args", [])
            full_cmd = f"{cmd} {' '.join(args_list)}".strip()
            lines.append(f"- **Command**: `{full_cmd}`")
            env = server.config.get("env", {})
            if env:
                lines.append(f"- **Env vars**: {', '.join(env.keys())}")
        else:
            url = server.config.get("url", "")
            lines.append(f"- **URL**: {url}")

        return "\n".join(lines)

    def handle_help(self, _args: list[str]) -> str:
        """Show help for /mcp commands."""
        return """**MCP Server Commands**

- `/mcp list` - List all configured servers with connection status
- `/mcp test [name]` - Test MCP server connections
- `/mcp add` - Add a new server (interactive)
- `/mcp add <name> <type> <cmd|url> [args]` - Add server directly
- `/mcp remove <name>` - Remove a server
- `/mcp enable <name>` - Enable a server
- `/mcp disable <name>` - Disable a server
- `/mcp status [name]` - Show server config details
- `/mcp help` - Show this help

**Server Types**
- `stdio` - Local process (command + args)
- `sse` - Server-Sent Events endpoint (URL)
- `http` - HTTP endpoint (URL)"""
