# Claude Agent SDK + E2B Sandbox Integration

**A graduate-level exploration of building autonomous AI agents with secure code execution capabilities**

---

## Overview

This project explores the intersection of two powerful technologies for building production-grade AI agents:

1. **Claude Agent SDK** - Anthropic's framework for building autonomous agents that can read files, run commands, search the web, and edit code
2. **E2B (Execution to Binary)** - An open-source infrastructure for running AI-generated code in secure, isolated cloud sandboxes

The goal is to build custom tools that enable Claude agents to execute code safely in isolated environments, combining the reasoning capabilities of Claude with the secure execution infrastructure of E2B.

---

## Conceptual Foundations

### The Agent Loop

At its core, an AI agent is a system that:
1. Receives a task or prompt
2. Reasons about what actions to take
3. Executes actions via **tools**
4. Observes results
5. Iterates until the task is complete

The Claude Agent SDK implements this loop with built-in tool execution, meaning you don't need to implement the mechanics of tool calling yourself. The SDK handles the agent loop autonomously:

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Find all TODO comments in the codebase and summarize them",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Glob", "Grep"])
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

### The Sandbox Paradigm

When agents execute code, security becomes paramount. E2B solves this by providing:

- **Isolation**: Each sandbox is a lightweight VM (~150ms startup)
- **Ephemeral environments**: Sandboxes are destroyed after use
- **Pre-installed dependencies**: Common data science libraries ready to use
- **Filesystem access**: Upload data, download results
- **Process control**: Run terminal commands with streaming output

```python
from e2b_code_interpreter import Sandbox

# Create an isolated execution environment
sbx = await Sandbox.create()

# Execute arbitrary code safely
execution = await sbx.runCode('print("Hello from the sandbox!")')
print(execution.logs)
```

### Why Combine Them?

The Claude Agent SDK provides excellent built-in tools (Read, Edit, Bash, Grep, etc.), but these execute on your local machine. For scenarios requiring:

- **Untrusted code execution** (user-submitted code, LLM-generated code)
- **Reproducible environments** (consistent dependencies across runs)
- **Parallel isolated sessions** (per-user sandboxes)
- **Data analysis with visualization** (matplotlib, plotly charts)

E2B sandboxes provide the secure execution layer that complements Claude's reasoning.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Application                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Claude Agent SDK                       │   │
│  │                                                          │   │
│  │   ┌──────────────────────────────────────────────────┐  │   │
│  │   │                  Agent Loop                       │  │   │
│  │   │  prompt → reason → tool_call → observe → repeat  │  │   │
│  │   └──────────────────────────────────────────────────┘  │   │
│  │                          │                               │   │
│  │   ┌──────────────────────┼──────────────────────────┐   │   │
│  │   │              Available Tools                     │   │   │
│  │   │                      │                           │   │   │
│  │   │  ┌─────────┐  ┌─────────┐  ┌─────────────────┐  │   │   │
│  │   │  │ Read    │  │ Edit    │  │ Custom E2B Tool │  │   │   │
│  │   │  │ Glob    │  │ Write   │  │                 │  │   │   │
│  │   │  │ Grep    │  │ Bash    │  │  ┌───────────┐  │  │   │   │
│  │   │  │ WebFetch│  │ ...     │  │  │ E2B API   │──┼──┼───┼───┤
│  │   │  └─────────┘  └─────────┘  │  └───────────┘  │  │   │   │
│  │   │                            └─────────────────┘  │   │   │
│  │   └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└───────────────────────────────────────────────────────────────┬─┘
                                                                │
                              ┌─────────────────────────────────┘
                              │
                              ▼
                 ┌────────────────────────────────────┐
                 │           E2B Cloud                │
                 │                                    │
                 │   ┌────────────┐ ┌────────────┐   │
                 │   │  Sandbox   │ │  Sandbox   │   │
                 │   │  (user 1)  │ │  (user 2)  │   │
                 │   │            │ │            │   │
                 │   │ ┌────────┐ │ │ ┌────────┐ │   │
                 │   │ │Python  │ │ │ │Python  │ │   │
                 │   │ │Runtime │ │ │ │Runtime │ │   │
                 │   │ └────────┘ │ │ └────────┘ │   │
                 │   │ ┌────────┐ │ │ ┌────────┐ │   │
                 │   │ │Files   │ │ │ │Files   │ │   │
                 │   │ └────────┘ │ │ └────────┘ │   │
                 │   └────────────┘ └────────────┘   │
                 └────────────────────────────────────┘
```

---

## Building Custom Tools

The Claude Agent SDK allows you to define custom tools using the MCP (Model Context Protocol) pattern. Here's how to build E2B-powered tools.

### Tool Anatomy

A custom tool requires:
1. **Name**: Unique identifier
2. **Description**: What the tool does (Claude reads this to decide when to use it)
3. **Schema**: Input parameters with types
4. **Handler**: Async function that executes the tool logic

```python
from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any

@tool(
    "tool_name",
    "Description of what this tool does - be specific for Claude to use it correctly",
    {"param1": str, "param2": int}  # Input schema
)
async def my_tool(args: dict[str, Any]) -> dict[str, Any]:
    # Tool implementation
    result = do_something(args["param1"], args["param2"])

    return {
        "content": [{
            "type": "text",
            "text": f"Result: {result}"
        }]
    }
```

### E2B Code Execution Tool

Here's a complete implementation of a tool that executes Python code in an E2B sandbox:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, query, ClaudeAgentOptions
from e2b_code_interpreter import Sandbox
from typing import Any
import asyncio
import json

# Global sandbox instance (or manage per-session)
sandbox: Sandbox = None

async def get_or_create_sandbox() -> Sandbox:
    global sandbox
    if sandbox is None:
        sandbox = await Sandbox.create()
    return sandbox


@tool(
    "execute_python",
    "Execute Python code in a secure isolated sandbox. Use this for data analysis, "
    "computations, or any code that needs to run safely. The sandbox has pandas, "
    "numpy, matplotlib, and other common libraries pre-installed.",
    {"code": str, "timeout": int}
)
async def execute_python(args: dict[str, Any]) -> dict[str, Any]:
    """Execute Python code in E2B sandbox."""
    code = args["code"]
    timeout = args.get("timeout", 30)

    try:
        sbx = await get_or_create_sandbox()
        execution = await sbx.runCode(code, timeout=timeout)

        # Collect outputs
        outputs = []

        # Standard output
        if execution.logs.stdout:
            outputs.append(f"stdout:\n{execution.logs.stdout}")

        # Standard error
        if execution.logs.stderr:
            outputs.append(f"stderr:\n{execution.logs.stderr}")

        # Errors
        if execution.error:
            outputs.append(f"Error:\n{execution.error.name}: {execution.error.value}")
            outputs.append(f"Traceback:\n{execution.error.traceback}")

        # Results (charts, data, etc.)
        for result in execution.results:
            if hasattr(result, 'text') and result.text:
                outputs.append(f"Result: {result.text}")
            if hasattr(result, 'png') and result.png:
                outputs.append("[Chart generated - PNG data available]")

        return {
            "content": [{
                "type": "text",
                "text": "\n\n".join(outputs) if outputs else "Code executed successfully (no output)"
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Execution failed: {str(e)}"
            }]
        }


@tool(
    "upload_file_to_sandbox",
    "Upload a file to the sandbox environment for use in code execution. "
    "Returns the path where the file is available in the sandbox.",
    {"filename": str, "content": str}
)
async def upload_file_to_sandbox(args: dict[str, Any]) -> dict[str, Any]:
    """Upload a file to the E2B sandbox."""
    try:
        sbx = await get_or_create_sandbox()
        filepath = await sbx.files.write(args["filename"], args["content"])

        return {
            "content": [{
                "type": "text",
                "text": f"File uploaded successfully to: {filepath}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Upload failed: {str(e)}"
            }]
        }


@tool(
    "read_file_from_sandbox",
    "Read a file from the sandbox environment. Use this to retrieve results, "
    "generated data, or any file created during code execution.",
    {"filepath": str}
)
async def read_file_from_sandbox(args: dict[str, Any]) -> dict[str, Any]:
    """Read a file from the E2B sandbox."""
    try:
        sbx = await get_or_create_sandbox()
        content = await sbx.files.read(args["filepath"])

        return {
            "content": [{
                "type": "text",
                "text": f"File contents:\n{content}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Read failed: {str(e)}"
            }]
        }


@tool(
    "list_sandbox_files",
    "List files in a directory within the sandbox. Useful for exploring "
    "what files exist after code execution.",
    {"path": str}
)
async def list_sandbox_files(args: dict[str, Any]) -> dict[str, Any]:
    """List files in a sandbox directory."""
    try:
        sbx = await get_or_create_sandbox()
        path = args.get("path", "/")
        files = await sbx.files.list(path)

        file_list = "\n".join([f"  {f.name}" for f in files])
        return {
            "content": [{
                "type": "text",
                "text": f"Files in {path}:\n{file_list}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"List failed: {str(e)}"
            }]
        }


@tool(
    "install_package",
    "Install a Python package in the sandbox using pip. Use this before "
    "running code that requires packages not pre-installed.",
    {"package": str}
)
async def install_package(args: dict[str, Any]) -> dict[str, Any]:
    """Install a pip package in the sandbox."""
    try:
        sbx = await get_or_create_sandbox()
        package = args["package"]

        # Run pip install
        execution = await sbx.runCode(f"!pip install {package}")

        return {
            "content": [{
                "type": "text",
                "text": f"Package installation output:\n{execution.logs.stdout}"
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Installation failed: {str(e)}"
            }]
        }


# Create the MCP server with all E2B tools
e2b_server = create_sdk_mcp_server(
    name="e2b-sandbox",
    version="1.0.0",
    tools=[
        execute_python,
        upload_file_to_sandbox,
        read_file_from_sandbox,
        list_sandbox_files,
        install_package
    ]
)
```

### Using E2B Tools with Claude Agent

```python
async def run_data_analysis_agent():
    """Run an agent with E2B sandbox capabilities."""

    async def message_generator():
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": """Analyze this data and create a visualization:

                sales_data = [
                    {"month": "Jan", "revenue": 12000, "costs": 8000},
                    {"month": "Feb", "revenue": 15000, "costs": 9000},
                    {"month": "Mar", "revenue": 18000, "costs": 10000},
                    {"month": "Apr", "revenue": 22000, "costs": 11000},
                ]

                Create a bar chart comparing revenue vs costs by month.
                Calculate profit margins and provide insights."""
            }
        }

    async for message in query(
        prompt=message_generator(),
        options=ClaudeAgentOptions(
            mcp_servers={"e2b-sandbox": e2b_server},
            allowed_tools=[
                "mcp__e2b-sandbox__execute_python",
                "mcp__e2b-sandbox__upload_file_to_sandbox",
                "mcp__e2b-sandbox__read_file_from_sandbox",
                "mcp__e2b-sandbox__list_sandbox_files",
                "mcp__e2b-sandbox__install_package",
            ]
        )
    ):
        if hasattr(message, 'result'):
            print(message.result)


if __name__ == "__main__":
    asyncio.run(run_data_analysis_agent())
```

---

## Advanced Patterns

### Pattern 1: Session-Scoped Sandboxes

For multi-turn conversations, maintain sandbox state across interactions:

```python
from dataclasses import dataclass
from typing import Optional
import uuid


@dataclass
class SandboxSession:
    session_id: str
    sandbox: Sandbox
    created_at: float


class SandboxManager:
    """Manage sandbox lifecycles across sessions."""

    def __init__(self):
        self.sessions: dict[str, SandboxSession] = {}

    async def get_sandbox(self, session_id: str) -> Sandbox:
        """Get or create a sandbox for a session."""
        if session_id not in self.sessions:
            sandbox = await Sandbox.create()
            self.sessions[session_id] = SandboxSession(
                session_id=session_id,
                sandbox=sandbox,
                created_at=time.time()
            )
        return self.sessions[session_id].sandbox

    async def cleanup_session(self, session_id: str):
        """Clean up a session's sandbox."""
        if session_id in self.sessions:
            await self.sessions[session_id].sandbox.close()
            del self.sessions[session_id]

    async def cleanup_stale(self, max_age_seconds: float = 300):
        """Clean up sandboxes older than max_age."""
        now = time.time()
        stale = [
            sid for sid, session in self.sessions.items()
            if now - session.created_at > max_age_seconds
        ]
        for sid in stale:
            await self.cleanup_session(sid)


# Global manager
sandbox_manager = SandboxManager()
```

### Pattern 2: Streaming Execution Output

For long-running code, stream output back to the user:

```python
@tool(
    "execute_python_streaming",
    "Execute Python code with streaming output. Use for long-running computations.",
    {"code": str}
)
async def execute_python_streaming(args: dict[str, Any]) -> dict[str, Any]:
    """Execute code with streaming output."""
    sbx = await get_or_create_sandbox()

    outputs = []

    async for event in sbx.runCode_streaming(args["code"]):
        if event.type == "stdout":
            outputs.append(f"[stdout] {event.data}")
        elif event.type == "stderr":
            outputs.append(f"[stderr] {event.data}")
        elif event.type == "result":
            outputs.append(f"[result] {event.data}")

    return {
        "content": [{
            "type": "text",
            "text": "\n".join(outputs)
        }]
    }
```

### Pattern 3: Combining Local and Remote Tools

Use both built-in tools (for local operations) and E2B tools (for sandboxed execution):

```python
async def run_hybrid_agent():
    """Agent with both local and sandboxed capabilities."""

    async def messages():
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": """Read the data file at ./data/sales.csv, then analyze it
                in a sandbox to create visualizations. Save insights to ./output/report.md"""
            }
        }

    async for message in query(
        prompt=messages(),
        options=ClaudeAgentOptions(
            mcp_servers={"e2b-sandbox": e2b_server},
            allowed_tools=[
                # Local file operations
                "Read",
                "Write",
                "Glob",
                # Sandboxed code execution
                "mcp__e2b-sandbox__execute_python",
                "mcp__e2b-sandbox__upload_file_to_sandbox",
            ]
        )
    ):
        if hasattr(message, 'result'):
            print(message.result)
```

### Pattern 4: Custom Sandbox Templates

E2B supports custom templates with pre-installed dependencies:

```python
# Using a custom template with specific packages
sbx = await Sandbox.create(template="data-science-heavy")

# Or build tools around specific templates
@tool(
    "execute_ml_code",
    "Execute machine learning code in a sandbox with sklearn, tensorflow, pytorch pre-installed.",
    {"code": str}
)
async def execute_ml_code(args: dict[str, Any]) -> dict[str, Any]:
    # Use ML-specific template
    sbx = await Sandbox.create(template="ml-template")
    execution = await sbx.runCode(args["code"])
    # ... handle results
```

---

## Error Handling Strategies

### Graceful Degradation

```python
@tool("execute_python_safe", "...", {"code": str})
async def execute_python_safe(args: dict[str, Any]) -> dict[str, Any]:
    try:
        sbx = await get_or_create_sandbox()
        execution = await sbx.runCode(args["code"], timeout=30)

        if execution.error:
            # Return error info for Claude to reason about
            return {
                "content": [{
                    "type": "text",
                    "text": f"Code execution failed:\n"
                            f"Error: {execution.error.name}\n"
                            f"Message: {execution.error.value}\n"
                            f"Traceback:\n{execution.error.traceback}\n\n"
                            f"Please fix the code and try again."
                }]
            }

        return {"content": [{"type": "text", "text": execution.logs.stdout}]}

    except asyncio.TimeoutError:
        return {
            "content": [{
                "type": "text",
                "text": "Execution timed out after 30 seconds. "
                        "Consider breaking the code into smaller chunks."
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Sandbox error: {str(e)}. The sandbox may need to be recreated."
            }]
        }
```

---

## Security Considerations

### Resource Limits

E2B sandboxes have built-in protections, but consider additional limits:

```python
EXECUTION_LIMITS = {
    "max_timeout": 60,           # Max execution time in seconds
    "max_output_size": 100_000,  # Max output characters
    "max_file_size": 10_000_000, # Max file size in bytes
}

@tool("execute_python_limited", "...", {"code": str})
async def execute_python_limited(args: dict[str, Any]) -> dict[str, Any]:
    code = args["code"]

    # Validate code doesn't contain obviously dangerous patterns
    dangerous_patterns = ["os.system", "subprocess", "eval(", "exec("]
    for pattern in dangerous_patterns:
        if pattern in code:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Code contains restricted pattern: {pattern}"
                }]
            }

    # Execute with limits
    sbx = await get_or_create_sandbox()
    execution = await sbx.runCode(
        code,
        timeout=EXECUTION_LIMITS["max_timeout"]
    )

    # Truncate large outputs
    output = execution.logs.stdout[:EXECUTION_LIMITS["max_output_size"]]

    return {"content": [{"type": "text", "text": output}]}
```

### Network Isolation

Control sandbox network access:

```python
# Create sandbox without network access
sbx = await Sandbox.create(
    allow_network=False  # No outbound network
)

# Or with specific allowlist
sbx = await Sandbox.create(
    allowed_hosts=["api.example.com"]
)
```

---

## Testing Tools

### Unit Testing Custom Tools

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_sandbox():
    """Create a mock sandbox for testing."""
    sandbox = AsyncMock()
    sandbox.runCode = AsyncMock(return_value=MagicMock(
        logs=MagicMock(stdout="test output", stderr=""),
        error=None,
        results=[]
    ))
    return sandbox


async def test_execute_python(mock_sandbox, monkeypatch):
    """Test the execute_python tool."""
    # Patch the sandbox creation
    monkeypatch.setattr(
        "your_module.get_or_create_sandbox",
        AsyncMock(return_value=mock_sandbox)
    )

    result = await execute_python({"code": "print('hello')"})

    assert "test output" in result["content"][0]["text"]
    mock_sandbox.runCode.assert_called_once_with("print('hello')", timeout=30)
```

### Integration Testing

```python
@pytest.mark.integration
async def test_full_agent_flow():
    """Test complete agent flow with E2B sandbox."""

    async def messages():
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": "Calculate 2 + 2 using Python"
            }
        }

    results = []
    async for message in query(
        prompt=messages(),
        options=ClaudeAgentOptions(
            mcp_servers={"e2b-sandbox": e2b_server},
            allowed_tools=["mcp__e2b-sandbox__execute_python"]
        )
    ):
        if hasattr(message, 'result'):
            results.append(message.result)

    assert any("4" in r for r in results)
```

---

## Project Structure

```
ClaudeAgentE2B/
├── README.md                    # This file
├── pyproject.toml              # Project dependencies
├── .env.example                # Environment variable template
│
├── src/
│   ├── __init__.py
│   ├── tools/                  # Custom tool definitions
│   │   ├── __init__.py
│   │   ├── e2b_executor.py     # E2B code execution tools
│   │   ├── file_tools.py       # Sandbox file operations
│   │   └── composite_tools.py  # Higher-level composed tools
│   │
│   ├── agents/                 # Agent configurations
│   │   ├── __init__.py
│   │   ├── data_analyst.py     # Data analysis agent
│   │   ├── code_runner.py      # General code execution agent
│   │   └── researcher.py       # Research + code agent
│   │
│   ├── sandbox/                # Sandbox management
│   │   ├── __init__.py
│   │   ├── manager.py          # Sandbox lifecycle management
│   │   └── templates.py        # Custom template definitions
│   │
│   └── utils/                  # Utilities
│       ├── __init__.py
│       └── streaming.py        # Output streaming helpers
│
├── tests/
│   ├── unit/
│   └── integration/
│
└── examples/
    ├── simple_execution.py     # Basic code execution
    ├── data_analysis.py        # Data analysis workflow
    └── multi_session.py        # Multi-user sandbox management
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Claude Code CLI installed
- E2B API key

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd ClaudeAgentE2B

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install claude-agent-sdk e2b-code-interpreter python-dotenv

# Set up environment
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
E2B_API_KEY=e2b_...
```

### First Run

```python
# examples/simple_execution.py
import asyncio
from src.tools.e2b_executor import e2b_server
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async def messages():
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": "Calculate the first 10 Fibonacci numbers using Python"
            }
        }

    async for message in query(
        prompt=messages(),
        options=ClaudeAgentOptions(
            mcp_servers={"e2b-sandbox": e2b_server},
            allowed_tools=["mcp__e2b-sandbox__execute_python"]
        )
    ):
        if hasattr(message, 'result'):
            print(message.result)

asyncio.run(main())
```

---

## Further Reading

### Claude Agent SDK
- [SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Custom Tools](https://platform.claude.com/docs/en/agent-sdk/custom-tools)
- [Hooks & Lifecycle](https://platform.claude.com/docs/en/agent-sdk/hooks)
- [Subagents](https://platform.claude.com/docs/en/agent-sdk/subagents)

### E2B
- [E2B Documentation](https://e2b.dev/docs)
- [Code Interpreter Guide](https://e2b.dev/docs/code-interpreting/analyze-data-with-ai)
- [Custom Templates](https://e2b.dev/docs/sandbox/templates)

### Model Context Protocol (MCP)
- [MCP Specification](https://modelcontextprotocol.io)
- [Building MCP Servers](https://modelcontextprotocol.io/docs/servers)

---

## License

MIT License - See LICENSE file for details.

---

*This project is an educational resource for understanding how to build production-grade AI agent tools that combine reasoning capabilities with secure code execution.*
