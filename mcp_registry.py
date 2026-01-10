"""
MCP Server Registry for Ralph-On-Shelf

Defines available MCP servers with metadata for auto-selection.
Each server includes keywords for prompt matching and authentication requirements.
"""

from dataclasses import dataclass
from typing import Literal

AuthType = Literal["open", "api_key", "oauth"]


@dataclass
class MCPServer:
    """Configuration for a remote MCP server."""

    name: str
    url: str
    auth_type: AuthType
    description: str
    categories: list[str]
    keywords: list[str]
    auth_env_var: str | None = None  # Environment variable for API key (if auth_type == "api_key")


# Registry of available MCP servers
# Servers are organized by authentication type for phased rollout
MCP_SERVERS: dict[str, MCPServer] = {
    # ============================================================
    # PHASE 1: Open/No-Auth Servers (Available Now)
    # ============================================================
    "exa-search": MCPServer(
        name="exa-search",
        url="https://mcp.exa.ai/mcp",
        auth_type="open",
        description="Web search and research powered by Exa AI",
        categories=["search", "research", "web"],
        keywords=[
            "search",
            "find",
            "look up",
            "lookup",
            "research",
            "web",
            "internet",
            "google",
            "browse",
            "query",
            "discover",
            "information",
            "latest",
            "recent",
            "news",
            "articles",
        ],
    ),
    "aws-knowledge": MCPServer(
        name="aws-knowledge",
        url="https://knowledge-mcp.global.api.aws",
        auth_type="open",
        description="AWS documentation, best practices, and cloud knowledge",
        categories=["cloud", "aws", "documentation", "infrastructure"],
        keywords=[
            "aws",
            "amazon",
            "cloud",
            "lambda",
            "s3",
            "ec2",
            "dynamodb",
            "rds",
            "cloudformation",
            "terraform",
            "serverless",
            "iam",
            "vpc",
            "cloudwatch",
            "sqs",
            "sns",
            "api gateway",
            "elastic",
            "beanstalk",
            "ecs",
            "eks",
            "fargate",
        ],
    ),
    # ============================================================
    # PHASE 2: API Key Servers (Requires .env configuration)
    # ============================================================
    "zapier": MCPServer(
        name="zapier",
        url="https://mcp.zapier.com/api/mcp/mcp",
        auth_type="api_key",
        description="Automation and integration with 5000+ apps via Zapier",
        categories=["automation", "integration", "workflow"],
        keywords=[
            "automate",
            "automation",
            "integrate",
            "integration",
            "workflow",
            "connect",
            "trigger",
            "zap",
            "zapier",
            "slack",
            "email",
            "sheets",
            "drive",
        ],
        auth_env_var="MCP_ZAPIER_API_KEY",
    ),
    "stripe": MCPServer(
        name="stripe",
        url="https://mcp.stripe.com/",
        auth_type="api_key",
        description="Payment processing and financial operations via Stripe",
        categories=["payments", "finance", "billing"],
        keywords=[
            "payment",
            "pay",
            "stripe",
            "billing",
            "invoice",
            "subscription",
            "charge",
            "refund",
            "customer",
            "checkout",
            "price",
            "product",
        ],
        auth_env_var="MCP_STRIPE_API_KEY",
    ),
    # ============================================================
    # PHASE 3: OAuth Servers (Requires token management)
    # ============================================================
    "github": MCPServer(
        name="github",
        url="https://api.githubcopilot.com/mcp",
        auth_type="oauth",
        description="GitHub repository management, issues, PRs, and code",
        categories=["code", "git", "development", "collaboration"],
        keywords=[
            "github",
            "git",
            "repository",
            "repo",
            "commit",
            "pull request",
            "pr",
            "issue",
            "branch",
            "merge",
            "clone",
            "fork",
            "code review",
        ],
    ),
    "notion": MCPServer(
        name="notion",
        url="https://mcp.notion.com/sse",
        auth_type="oauth",
        description="Notion workspace management - pages, databases, and content",
        categories=["documentation", "wiki", "project management"],
        keywords=[
            "notion",
            "document",
            "wiki",
            "page",
            "database",
            "workspace",
            "notes",
            "knowledge base",
            "documentation",
        ],
    ),
    "linear": MCPServer(
        name="linear",
        url="https://mcp.linear.app/sse",
        auth_type="oauth",
        description="Linear issue tracking and project management",
        categories=["project management", "issues", "agile"],
        keywords=[
            "linear",
            "issue",
            "ticket",
            "task",
            "project",
            "sprint",
            "backlog",
            "kanban",
            "agile",
            "track",
            "bug",
        ],
    ),
    "asana": MCPServer(
        name="asana",
        url="https://mcp.asana.com/sse",
        auth_type="oauth",
        description="Asana task and project management",
        categories=["project management", "tasks", "collaboration"],
        keywords=[
            "asana",
            "task",
            "project",
            "team",
            "assign",
            "due date",
            "milestone",
            "portfolio",
        ],
    ),
    "supabase": MCPServer(
        name="supabase",
        url="https://mcp.supabase.com/mcp",
        auth_type="oauth",
        description="Supabase database and backend operations",
        categories=["database", "backend", "api"],
        keywords=[
            "supabase",
            "database",
            "postgres",
            "sql",
            "table",
            "query",
            "auth",
            "storage",
            "realtime",
        ],
    ),
    "posthog": MCPServer(
        name="posthog",
        url="https://mcp.posthog.com/sse",
        auth_type="api_key",
        description="PostHog analytics, insights, errors, feature flags, and SQL queries",
        categories=["analytics", "product", "data"],
        keywords=[
            "posthog",
            "analytics",
            "visitors",
            "users",
            "events",
            "insights",
            "metrics",
            "pageviews",
            "sessions",
            "feature flags",
            "errors",
            "trends",
            "funnels",
            "retention",
        ],
        auth_env_var="POSTHOG_API_KEY",
    ),
    "wandb": MCPServer(
        name="wandb",
        url="https://mcp.withwandb.com/sse",
        auth_type="api_key",
        description="Weights & Biases ML experiment tracking, runs, sweeps, and Weave traces",
        categories=["ml", "experiments", "tracking", "ai"],
        keywords=[
            "wandb",
            "weights",
            "biases",
            "experiment",
            "run",
            "sweep",
            "model",
            "training",
            "ml",
            "machine learning",
            "metrics",
            "artifacts",
            "weave",
            "traces",
        ],
        auth_env_var="WANDB_API",
    ),
}


def get_server(name: str) -> MCPServer | None:
    """Get a server by name."""
    return MCP_SERVERS.get(name)


def get_servers_by_auth_type(auth_type: AuthType) -> list[MCPServer]:
    """Get all servers of a specific authentication type."""
    return [s for s in MCP_SERVERS.values() if s.auth_type == auth_type]


def get_open_servers() -> list[MCPServer]:
    """Get all servers that require no authentication."""
    return get_servers_by_auth_type("open")


def get_all_servers() -> list[MCPServer]:
    """Get all registered servers."""
    return list(MCP_SERVERS.values())


def list_servers_summary() -> str:
    """Return a formatted summary of all available servers."""
    lines = ["Available MCP Servers:", "=" * 50]

    for auth_type in ["open", "api_key", "oauth"]:
        servers = get_servers_by_auth_type(auth_type)
        if servers:
            auth_label = {
                "open": "No Authentication Required",
                "api_key": "API Key Required",
                "oauth": "OAuth Required",
            }[auth_type]
            lines.append(f"\n{auth_label}:")
            lines.append("-" * 30)
            for server in servers:
                status = "Ready" if auth_type == "open" else "Configure .env"
                lines.append(f"  {server.name}: {server.description} [{status}]")

    return "\n".join(lines)
