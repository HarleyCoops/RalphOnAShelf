"""
Ralph-On-Shelf: Launch Claude Agent SDK inside E2B cloud sandbox with Ralph Wiggum loop.

This runs the agent in the cloud (Linux) with self-referential iteration until completion.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

# Workspace directory inside sandbox where all outputs are saved
SANDBOX_WORKSPACE = "/home/user/workspace"

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()


# The agent code that runs INSIDE the E2B sandbox
AGENT_CODE = '''
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


class RalphLoop:
    """
    Ralph Wiggum Loop: Self-referential agent iteration in E2B sandbox.
    """

    def __init__(
        self,
        prompt: str,
        max_iterations: int = 10,
        completion_promise: str = "COMPLETE",
        timeout: int = 600,
        output_dir: str | None = None
    ):
        self.prompt = prompt
        self.max_iterations = max_iterations
        self.completion_promise = completion_promise
        self.timeout = timeout
        self.output_dir = output_dir or os.path.join(os.getcwd(), "ralph_output")
        self.current_iteration = 0
        self.sandbox = None
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")

    def _create_sandbox(self):
        """Create and setup the E2B sandbox."""
        print("[ralph] creating sandbox...")
        sandbox_factory = getattr(Sandbox, "create", None)
        if callable(sandbox_factory):
            self.sandbox = sandbox_factory(timeout=self.timeout)
        else:
            self.sandbox = Sandbox(timeout=self.timeout)
        print(f"[ralph] sandbox: {self.sandbox.sandbox_id}")

        # Install dependencies
        print("[ralph] installing dependencies...")
        result = self.sandbox.run_code("""
import subprocess
subprocess.run(['pip', 'install', 'claude-agent-sdk', 'nest_asyncio'], capture_output=True)
print("done")
""")
        if result.logs.stdout:
            print("".join(result.logs.stdout).strip())

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
                    local_path.write_text(content, encoding='utf-8')

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

        agent_code = AGENT_CODE.format(
            api_key=self.api_key,
            prompt=self.prompt.replace('"""', '\\"\\"\\"').replace('{', '{{').replace('}', '}}'),
            iteration=self.current_iteration,
            max_iterations=self.max_iterations,
            completion_promise=self.completion_promise
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
        print(f"[ralph] starting loop")
        print(f"[ralph] prompt: {self.prompt[:80]}...")
        print(f"[ralph] max_iterations: {self.max_iterations}")
        print(f"[ralph] completion_signal: {self.completion_promise}")

        history = []
        downloaded_files = []
        status = "max_iterations_reached"

        try:
            self._create_sandbox()

            while self.current_iteration < self.max_iterations:
                print(f"\n[ralph] iteration {self.current_iteration + 1}/{self.max_iterations}")

                output, is_complete = self._run_iteration()
                history.append({
                    "iteration": self.current_iteration,
                    "output": output[:2000],
                    "timestamp": datetime.now().isoformat()
                })

                if is_complete:
                    status = "completed"
                    print(f"\n[ralph] task completed")
                    break

                print(f"[ralph] continuing...")

            # Download all workspace files before cleanup
            if self.sandbox:
                print(f"\n[ralph] retrieving workspace files...")
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
            "downloaded_files": downloaded_files
        }


def launch_ralph(
    prompt: str,
    max_iterations: int = 10,
    completion_promise: str = "COMPLETE",
    timeout: int = 600,
    output_dir: str | None = None
) -> dict:
    """
    Launch a Ralph Wiggum loop.

    Args:
        prompt: The task for the agent to work on
        max_iterations: Maximum iterations before stopping (default 10)
        completion_promise: Text that signals task completion (default "COMPLETE")
        timeout: Sandbox timeout in seconds (default 10 minutes)
        output_dir: Local directory to save workspace files (default: ./ralph_output)

    Returns:
        dict with status, iterations, output history, and downloaded files
    """
    ralph = RalphLoop(
        prompt=prompt,
        max_iterations=max_iterations,
        completion_promise=completion_promise,
        timeout=timeout,
        output_dir=output_dir
    )
    return ralph.run()


def main():
    """Test the Ralph Wiggum loop."""
    prompt = """Create a Python script that:
1. Calculates the first 20 Fibonacci numbers
2. Saves them to a file called fibonacci.txt
3. Reads the file back and prints the contents

Output COMPLETE when you have verified the file was created and contains the correct numbers."""

    result = launch_ralph(
        prompt=prompt,
        max_iterations=5,
        completion_promise="COMPLETE"
    )

    print(f"\n[ralph] result: {result['status']}")
    print(f"[ralph] iterations: {result['iterations']}/{result['max_iterations']}")


if __name__ == "__main__":
    main()
