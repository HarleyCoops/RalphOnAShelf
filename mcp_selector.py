"""
MCP Server Selector for Ralph-On-Shelf

Analyzes prompts and selects relevant MCP servers based on keyword matching.
Returns configurations ready for the Anthropic API mcp_servers parameter.
"""

import os
import re
from dataclasses import dataclass

from mcp_registry import (
    MCP_SERVERS,
    AuthType,
    MCPServer,
    get_open_servers,
    get_servers_by_auth_type,
)


@dataclass
class MCPSelection:
    """Result of MCP server selection."""

    servers: list[dict]  # Ready for Anthropic API mcp_servers param
    toolsets: list[dict]  # Ready for Anthropic API tools param
    selected_names: list[str]  # Names of selected servers
    skipped: list[str]  # Servers that matched but lacked auth


def _normalize_text(text: str) -> str:
    """Normalize text for keyword matching."""
    return re.sub(r"[^\w\s]", " ", text.lower())


def _keyword_score(prompt: str, server: MCPServer) -> int:
    """
    Calculate relevance score based on keyword matches.

    Returns number of keyword matches found in the prompt.
    """
    normalized_prompt = _normalize_text(prompt)
    score = 0

    for keyword in server.keywords:
        # Check for whole word matches (with word boundaries)
        if re.search(rf"\b{re.escape(keyword.lower())}\b", normalized_prompt):
            score += 1

    # Bonus points for category matches
    for category in server.categories:
        if category.lower() in normalized_prompt:
            score += 2

    # Bonus for exact server name mention
    if server.name.lower() in normalized_prompt:
        score += 5

    return score


def _has_valid_auth(server: MCPServer) -> tuple[bool, str | None]:
    """
    Check if server has valid authentication configured.

    Returns (is_valid, auth_token_or_none).
    """
    if server.auth_type == "open":
        return True, None

    if server.auth_type == "api_key":
        if server.auth_env_var:
            token = os.getenv(server.auth_env_var)
            if token:
                return True, token
        return False, None

    if server.auth_type == "oauth":
        # Check multiple possible env var patterns for OAuth tokens
        name_upper = server.name.upper().replace("-", "_")
        possible_vars = [
            f"MCP_{name_upper}_TOKEN",  # MCP_GITHUB_TOKEN
            f"{name_upper}_TOKEN",       # GITHUB_TOKEN
            f"{name_upper}_API_KEY",     # LINEAR_API_KEY
            f"{name_upper}_API_TOKEN",   # GITHUB_API_TOKEN
            f"GH_TOKEN" if server.name == "github" else None,  # Common GitHub alias
        ]
        for var in possible_vars:
            if var:
                token = os.getenv(var)
                if token:
                    return True, token
        return False, None

    return False, None


def _build_server_config(server: MCPServer, auth_token: str | None) -> dict:
    """Build the mcp_servers entry for the Anthropic API."""
    config = {
        "type": "url",
        "url": server.url,
        "name": server.name,
    }
    if auth_token:
        config["authorization_token"] = auth_token
    return config


def _build_toolset_config(server: MCPServer) -> dict:
    """Build the tools entry for the Anthropic API."""
    return {
        "type": "mcp_toolset",
        "mcp_server_name": server.name,
    }


def select_mcp_servers(
    prompt: str,
    allowed_auth_types: list[AuthType] | None = None,
    explicit_servers: list[str] | None = None,
    min_score: int = 1,
    max_servers: int = 5,
) -> MCPSelection:
    """
    Analyze prompt and select relevant MCP servers.

    Args:
        prompt: The task prompt to analyze
        allowed_auth_types: List of auth types to consider (default: ["open"])
        explicit_servers: Explicitly requested server names (overrides auto-select)
        min_score: Minimum keyword score to include a server
        max_servers: Maximum number of servers to select

    Returns:
        MCPSelection with server configs ready for Anthropic API
    """
    if allowed_auth_types is None:
        allowed_auth_types = ["open"]

    servers: list[dict] = []
    toolsets: list[dict] = []
    selected_names: list[str] = []
    skipped: list[str] = []

    # If explicit servers requested, use those
    if explicit_servers:
        for name in explicit_servers:
            if name in MCP_SERVERS:
                server = MCP_SERVERS[name]
                has_auth, token = _has_valid_auth(server)
                if has_auth:
                    servers.append(_build_server_config(server, token))
                    toolsets.append(_build_toolset_config(server))
                    selected_names.append(name)
                else:
                    skipped.append(f"{name} (missing auth: {server.auth_env_var or 'oauth token'})")
        return MCPSelection(servers, toolsets, selected_names, skipped)

    # Auto-select based on prompt analysis
    candidates: list[tuple[int, MCPServer]] = []

    for server in MCP_SERVERS.values():
        # Filter by allowed auth types
        if server.auth_type not in allowed_auth_types:
            continue

        # Calculate relevance score
        score = _keyword_score(prompt, server)
        if score >= min_score:
            candidates.append((score, server))

    # Sort by score (descending) and take top N
    candidates.sort(key=lambda x: x[0], reverse=True)

    for score, server in candidates[:max_servers]:
        has_auth, token = _has_valid_auth(server)
        if has_auth:
            servers.append(_build_server_config(server, token))
            toolsets.append(_build_toolset_config(server))
            selected_names.append(server.name)
        else:
            skipped.append(f"{server.name} (missing auth)")

    return MCPSelection(servers, toolsets, selected_names, skipped)


def select_all_open_servers() -> MCPSelection:
    """Select all servers that require no authentication."""
    servers: list[dict] = []
    toolsets: list[dict] = []
    selected_names: list[str] = []

    for server in get_open_servers():
        servers.append(_build_server_config(server, None))
        toolsets.append(_build_toolset_config(server))
        selected_names.append(server.name)

    return MCPSelection(servers, toolsets, selected_names, [])


def get_available_servers(auth_types: list[AuthType] | None = None) -> list[str]:
    """
    Get list of servers that are currently available (have valid auth).

    Args:
        auth_types: Filter by auth types (default: all)

    Returns:
        List of available server names
    """
    available = []

    for server in MCP_SERVERS.values():
        if auth_types and server.auth_type not in auth_types:
            continue
        has_auth, _ = _has_valid_auth(server)
        if has_auth:
            available.append(server.name)

    return available


# Convenience function for common use case
def auto_select(prompt: str) -> MCPSelection:
    """
    Auto-select MCP servers for a prompt using all available authentication.

    This checks which servers have valid auth configured and selects
    from those based on prompt analysis.
    """
    # Determine which auth types have any configured servers
    available_auth: list[AuthType] = ["open"]  # Always include open

    # Check if any API key servers are configured
    for server in get_servers_by_auth_type("api_key"):
        has_auth, _ = _has_valid_auth(server)
        if has_auth:
            available_auth.append("api_key")
            break

    # Check if any OAuth servers are configured
    for server in get_servers_by_auth_type("oauth"):
        has_auth, _ = _has_valid_auth(server)
        if has_auth:
            available_auth.append("oauth")
            break

    return select_mcp_servers(prompt, allowed_auth_types=available_auth, min_score=2)
