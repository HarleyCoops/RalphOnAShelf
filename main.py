"""
Ralph-On-Shelf: Launch Claude agents inside E2B cloud sandbox with Ralph Wiggum loop.

This runs the agent in the cloud (Linux) with self-referential iteration until completion.
Supports MCP (Model Context Protocol) connectors for external tool access.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

from mcp_selector import MCPSelection, auto_select, select_mcp_servers

# Workspace directory inside sandbox where all outputs are saved
SANDBOX_WORKSPACE = "/home/user/workspace"

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()


# ============================================================
# AGENT CODE: Non-MCP version using claude-agent-sdk
# ============================================================
AGENT_CODE_SDK = '''
import asyncio
import os
import json
import nest_asyncio

# Allow nested event loops (needed in Jupyter/E2B environment)
nest_asyncio.apply()

# Set API key in sandbox environment
os.environ["ANTHROPIC_API_KEY"] = "{api_key}"

from claude_agent_sdk import ClaudeAgentOptions, query

# Workspace directory for all outputs
WORKSPACE = "/home/user/workspace"
os.makedirs(WORKSPACE, exist_ok=True)
os.chdir(WORKSPACE)

# Read previous iteration context if it exists
previous_context = ""
try:
    with open("/home/user/ralph_state.json", "r") as f:
        state = json.load(f)
        if state.get("history"):
            previous_context = "\\n\\n--- Previous Iteration Results ---\\n"
            for i, h in enumerate(state["history"][-3:], 1):  # Last 3 iterations
                previous_context += f"\\nIteration {{i}}:\\n{{h[:500]}}...\\n"
except:
    pass

async def run_agent():
    prompt = """{prompt}"""
    iteration = {iteration}
    max_iterations = {max_iterations}
    completion_promise = "{completion_promise}"

    full_prompt = f"""{{prompt}}

ITERATION: {{iteration}} / {{max_iterations}}
{{previous_context if previous_context else ""}}

IMPORTANT:
- You are in a Ralph Wiggum loop - working autonomously until the task is complete
- Output "{{completion_promise}}" when you have fully completed the task
- WORKSPACE: You are in /home/user/workspace - save ALL outputs here (they will be downloaded)
- You have {{max_iterations - iteration}} iterations remaining
- Do not use emojis or special characters in your output - keep it plain text
"""

    # Configure for AUTONOMOUS execution - accept edits but avoid strict root check
    options = ClaudeAgentOptions(
        permission_mode="acceptEdits",
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        cwd=WORKSPACE
    )

    result_text = ""
    async for message in query(
        prompt=full_prompt,
        options=options
    ):
        if hasattr(message, "result"):
            result_text = message.result
            # result is captured for completion check, already printed via content blocks
        elif hasattr(message, "content"):
            # Filter to only show TextBlock content, skip tool blocks
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)

    # Save state for next iteration
    try:
        try:
            with open("/home/user/ralph_state.json", "r") as f:
                state = json.load(f)
        except:
            state = {{"history": []}}

        state["history"].append(result_text[:1000] if result_text else "No result")
        state["last_iteration"] = iteration

        with open("/home/user/ralph_state.json", "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"[ralph] warning: could not save state: {{e}}")

    # Check for completion
    if completion_promise in result_text:
        print(f"\\n[ralph] completion signal detected")

asyncio.run(run_agent())
'''


# ============================================================
# AGENT CODE: MCP-enabled version using direct Anthropic API
# ============================================================
AGENT_CODE_MCP = '''
import os
import json

# Set API key in sandbox environment
os.environ["ANTHROPIC_API_KEY"] = "{api_key}"

import anthropic

# Workspace directory for all outputs
WORKSPACE = "/home/user/workspace"
os.makedirs(WORKSPACE, exist_ok=True)
os.chdir(WORKSPACE)

# Read previous iteration context if it exists
previous_context = ""
try:
    with open("/home/user/ralph_state.json", "r") as f:
        state = json.load(f)
        if state.get("history"):
            previous_context = "\\n\\n--- Previous Iteration Results ---\\n"
            for i, h in enumerate(state["history"][-3:], 1):
                previous_context += f"\\nIteration {{i}}:\\n{{h[:500]}}...\\n"
except:
    pass

def run_agent():
    prompt = """{prompt}"""
    iteration = {iteration}
    max_iterations = {max_iterations}
    completion_promise = "{completion_promise}"

    # MCP server configurations (injected)
    mcp_servers = {mcp_servers_json}
    mcp_toolsets = {mcp_toolsets_json}

    full_prompt = f"""{{prompt}}

ITERATION: {{iteration}} / {{max_iterations}}
{{previous_context if previous_context else ""}}

IMPORTANT:
- You are in a Ralph Wiggum loop - working autonomously until the task is complete
- Output "{{completion_promise}}" when you have fully completed the task
- WORKSPACE: You are in /home/user/workspace - save ALL outputs here (they will be downloaded)
- You have {{max_iterations - iteration}} iterations remaining
- Do not use emojis or special characters in your output - keep it plain text
- You have access to MCP tools from external services - use them when relevant to the task
"""

    client = anthropic.Anthropic()
    messages = [{{"role": "user", "content": full_prompt}}]
    result_text = ""

    # Agentic loop - continue until no more tool calls
    max_turns = 20  # Safety limit
    turn = 0

    while turn < max_turns:
        turn += 1

        # Build API request
        request_params = {{
            "model": "claude-sonnet-4-5",
            "max_tokens": 8096,
            "messages": messages,
        }}

        # Add MCP if configured
        if mcp_servers:
            request_params["mcp_servers"] = mcp_servers
            request_params["tools"] = mcp_toolsets
            response = client.beta.messages.create(
                **request_params,
                betas=["mcp-client-2025-11-20"]
            )
        else:
            response = client.messages.create(**request_params)

        # Process response
        assistant_content = []
        has_tool_use = False

        for block in response.content:
            if block.type == "text":
                print(block.text)
                result_text += block.text
                assistant_content.append({{"type": "text", "text": block.text}})

            elif block.type == "tool_use":
                # Regular tool use (if we add non-MCP tools later)
                has_tool_use = True
                assistant_content.append({{
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                }})
                print(f"[tool] {{block.name}}: {{json.dumps(block.input)[:200]}}")

            elif block.type == "mcp_tool_use":
                # MCP tool use - handled automatically by API
                has_tool_use = True
                assistant_content.append({{
                    "type": "mcp_tool_use",
                    "id": block.id,
                    "name": block.name,
                    "server_name": block.server_name,
                    "input": block.input
                }})
                print(f"[mcp-tool] {{block.server_name}}/{{block.name}}: {{json.dumps(block.input)[:200]}}")

            elif block.type == "mcp_tool_result":
                # MCP tool results are included in the response
                result_content = ""
                if hasattr(block, "content"):
                    for item in block.content:
                        if hasattr(item, "text"):
                            result_content = item.text[:500]
                print(f"[mcp-result] {{result_content[:200]}}...")

        # Add assistant message to conversation
        messages.append({{"role": "assistant", "content": assistant_content}})

        # Check if we need to continue (tool use requires continuation)
        if response.stop_reason == "end_turn" or not has_tool_use:
            break

        # For MCP tools, the API handles tool execution automatically
        # We just need to continue the conversation
        if response.stop_reason == "tool_use":
            # Add a continuation prompt for next turn
            messages.append({{
                "role": "user",
                "content": "Continue with the task. If you used tools, process the results and continue working."
            }})

    # Save state for next iteration
    try:
        try:
            with open("/home/user/ralph_state.json", "r") as f:
                state = json.load(f)
        except:
            state = {{"history": []}}

        state["history"].append(result_text[:1000] if result_text else "No result")
        state["last_iteration"] = iteration

        with open("/home/user/ralph_state.json", "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"[ralph] warning: could not save state: {{e}}")

    # Check for completion
    if completion_promise in result_text:
        print(f"\\n[ralph] completion signal detected")

run_agent()
'''


class RalphLoop:
    """
    Ralph Wiggum Loop: Self-referential agent iteration in E2B sandbox.

    Supports MCP (Model Context Protocol) connectors for external tool access.
    """

    def __init__(
        self,
        prompt: str,
        max_iterations: int = 10,
        completion_promise: str = "COMPLETE",
        timeout: int = 600,
        output_dir: str | None = None,
        mcp_mode: str = "auto",  # "auto", "none", or comma-separated server names
    ):
        self.prompt = prompt
        self.max_iterations = max_iterations
        self.completion_promise = completion_promise
        self.timeout = timeout
        self.output_dir = output_dir or os.path.join(os.getcwd(), "ralph_output")
        self.current_iteration = 0
        self.sandbox = None
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.mcp_mode = mcp_mode
        self.mcp_selection: MCPSelection | None = None

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")

        # Select MCP servers based on mode
        self._configure_mcp()

    def _configure_mcp(self):
        """Configure MCP servers based on mode setting."""
        if self.mcp_mode == "none":
            self.mcp_selection = None
            return

        if self.mcp_mode == "auto":
            self.mcp_selection = auto_select(self.prompt)
        else:
            # Explicit server names
            server_names = [s.strip() for s in self.mcp_mode.split(",")]
            self.mcp_selection = select_mcp_servers(
                self.prompt,
                explicit_servers=server_names,
                allowed_auth_types=["open", "api_key", "oauth"],
            )

        # Log MCP configuration
        if self.mcp_selection and self.mcp_selection.selected_names:
            print(f"[ralph] MCP servers: {', '.join(self.mcp_selection.selected_names)}")
        if self.mcp_selection and self.mcp_selection.skipped:
            print(f"[ralph] MCP skipped (no auth): {', '.join(self.mcp_selection.skipped)}")

    def _create_sandbox(self):
        """Create and setup the E2B sandbox."""
        print("[ralph] creating sandbox...")
        sandbox_factory = getattr(Sandbox, "create", None)
        if callable(sandbox_factory):
            self.sandbox = sandbox_factory(timeout=self.timeout)
        else:
            self.sandbox = Sandbox(timeout=self.timeout)
        print(f"[ralph] sandbox: {self.sandbox.sandbox_id}")

        # Install dependencies based on mode
        deps = ["nest_asyncio"]
        if self._use_mcp_mode():
            deps.append("anthropic")
        else:
            deps.append("claude-agent-sdk")

        print(f"[ralph] installing: {', '.join(deps)}")
        result = self.sandbox.run_code(f"""
import subprocess
subprocess.run(['pip', 'install'] + {deps}, capture_output=True)
print("done")
""")
        if result.logs.stdout:
            print("".join(result.logs.stdout).strip())

    def _use_mcp_mode(self) -> bool:
        """Check if we should use MCP mode."""
        return self.mcp_selection is not None and len(self.mcp_selection.selected_names) > 0

    def _download_workspace(self) -> list[str]:
        """
        Download all files from the sandbox workspace to local output_dir.

        Returns:
            List of downloaded file paths
        """
        downloaded = []

        # List all files in workspace recursively
        result = self.sandbox.run_code(f"""
import os
import json

workspace = "{SANDBOX_WORKSPACE}"
files = []
for root, dirs, filenames in os.walk(workspace):
    # Skip hidden directories
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for filename in filenames:
        if not filename.startswith('.'):
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, workspace)
            files.append(rel_path)
print(json.dumps(files))
""")

        if not result.logs.stdout:
            print("[ralph] no files found in workspace")
            return downloaded

        try:
            files = json.loads("".join(result.logs.stdout).strip())
        except json.JSONDecodeError:
            print("[ralph] failed to parse file list")
            return downloaded

        if not files:
            print("[ralph] workspace is empty")
            return downloaded

        # Create local output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        print(f"[ralph] downloading {len(files)} file(s) to {self.output_dir}")

        for rel_path in files:
            remote_path = f"{SANDBOX_WORKSPACE}/{rel_path}"
            local_path = Path(self.output_dir) / rel_path

            try:
                # Create subdirectories if needed
                local_path.parent.mkdir(parents=True, exist_ok=True)

                # Download file content
                content = self.sandbox.files.read(remote_path)

                # Write to local file (handle both text and binary)
                if isinstance(content, bytes):
                    local_path.write_bytes(content)
                else:
                    local_path.write_text(content, encoding="utf-8")

                downloaded.append(str(local_path))
                print(f"[ralph] downloaded: {rel_path}")

            except Exception as e:
                print(f"[ralph] failed to download {rel_path}: {e}")

        return downloaded

    def _run_iteration(self) -> tuple[str, bool]:
        """
        Run a single iteration of the Ralph loop.

        Returns:
            tuple of (output, is_complete)
        """
        self.current_iteration += 1

        # Escape prompt for string formatting
        escaped_prompt = (
            self.prompt.replace('"""', '\\"\\"\\"').replace("{", "{{").replace("}", "}}")
        )

        if self._use_mcp_mode():
            # Use MCP-enabled agent code
            agent_code = AGENT_CODE_MCP.format(
                api_key=self.api_key,
                prompt=escaped_prompt,
                iteration=self.current_iteration,
                max_iterations=self.max_iterations,
                completion_promise=self.completion_promise,
                mcp_servers_json=json.dumps(self.mcp_selection.servers),
                mcp_toolsets_json=json.dumps(self.mcp_selection.toolsets),
            )
        else:
            # Use SDK-based agent code (no MCP)
            agent_code = AGENT_CODE_SDK.format(
                api_key=self.api_key,
                prompt=escaped_prompt,
                iteration=self.current_iteration,
                max_iterations=self.max_iterations,
                completion_promise=self.completion_promise,
            )

        result = self.sandbox.run_code(agent_code)

        output = ""
        if result.logs.stdout:
            output = "".join(result.logs.stdout)
            print(output)

        if result.logs.stderr:
            print(f"[ralph] stderr: {''.join(result.logs.stderr)}")

        if result.error:
            print(f"[ralph] error: {result.error.name}: {result.error.value}")

        is_complete = self.completion_promise in output
        return output, is_complete

    def run(self) -> dict:
        """
        Run the full Ralph Wiggum loop until completion or max iterations.

        Returns:
            dict with status, iterations, and output history
        """
        print("[ralph] starting loop")
        print(f"[ralph] prompt: {self.prompt[:80]}...")
        print(f"[ralph] max_iterations: {self.max_iterations}")
        print(f"[ralph] completion_signal: {self.completion_promise}")
        print(f"[ralph] mode: {'MCP' if self._use_mcp_mode() else 'SDK'}")

        history = []
        downloaded_files = []
        status = "max_iterations_reached"

        try:
            self._create_sandbox()

            while self.current_iteration < self.max_iterations:
                print(f"\n[ralph] iteration {self.current_iteration + 1}/{self.max_iterations}")

                output, is_complete = self._run_iteration()
                history.append(
                    {
                        "iteration": self.current_iteration,
                        "output": output[:2000],
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                if is_complete:
                    status = "completed"
                    print("\n[ralph] task completed")
                    break

                print("[ralph] continuing...")

            # Download all workspace files before cleanup
            if self.sandbox:
                print("\n[ralph] retrieving workspace files...")
                downloaded_files = self._download_workspace()

        finally:
            if self.sandbox:
                print(f"[ralph] cleanup: {self.sandbox.sandbox_id}")
                self.sandbox.kill()

        return {
            "status": status,
            "iterations": self.current_iteration,
            "max_iterations": self.max_iterations,
            "history": history,
            "prompt": self.prompt,
            "completion_promise": self.completion_promise,
            "output_dir": self.output_dir,
            "downloaded_files": downloaded_files,
            "mcp_servers": (self.mcp_selection.selected_names if self.mcp_selection else []),
        }


def launch_ralph(
    prompt: str,
    max_iterations: int = 10,
    completion_promise: str = "COMPLETE",
    timeout: int = 600,
    output_dir: str | None = None,
    mcp: str = "auto",
) -> dict:
    """
    Launch a Ralph Wiggum loop.

    Args:
        prompt: The task for the agent to work on
        max_iterations: Maximum iterations before stopping (default 10)
        completion_promise: Text that signals task completion (default "COMPLETE")
        timeout: Sandbox timeout in seconds (default 10 minutes)
        output_dir: Local directory to save workspace files (default: ./ralph_output)
        mcp: MCP mode - "auto" (select based on prompt), "none", or comma-separated
             server names like "exa-search,aws-knowledge"

    Returns:
        dict with status, iterations, output history, and downloaded files
    """
    ralph = RalphLoop(
        prompt=prompt,
        max_iterations=max_iterations,
        completion_promise=completion_promise,
        timeout=timeout,
        output_dir=output_dir,
        mcp_mode=mcp,
    )
    return ralph.run()


def main():
    """Test the Ralph Wiggum loop with MCP."""
    # Test with a search task that should trigger Exa MCP
    prompt = """Search the web for the latest Python 3.13 features and create a summary.

Save the summary to a file called python313_features.txt in the workspace.

Output COMPLETE when done."""

    result = launch_ralph(
        prompt=prompt,
        max_iterations=5,
        completion_promise="COMPLETE",
        mcp="auto",  # Auto-select MCP servers based on prompt
    )

    print(f"\n[ralph] result: {result['status']}")
    print(f"[ralph] iterations: {result['iterations']}/{result['max_iterations']}")
    print(f"[ralph] MCP servers used: {result.get('mcp_servers', [])}")


if __name__ == "__main__":
    main()
