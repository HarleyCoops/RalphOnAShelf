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
from mcp_registry import MCP_SERVERS, get_all_servers

# Workspace directory inside sandbox where all outputs are saved
SANDBOX_WORKSPACE = "/home/user/workspace"


# ============================================================
# WIGGUM PLANNER: Analyzes task and creates execution plan
# Runs LOCALLY before sandbox launch
# ============================================================
class WiggumPlanner:
    """
    Chief Wiggum: The planning orchestrator.

    Analyzes the user's task, breaks it into subtasks (todos),
    and assigns the most efficient MCPs to each subtask.
    """

    PLANNING_PROMPT = '''You are Chief Wiggum, a task planning AI. Analyze this task and create an execution plan.

TASK: {prompt}

AVAILABLE MCP TOOLS:
{mcp_list}

Your job:
1. Break the task into 1-5 concrete subtasks (todos)
2. For each subtask, assign ONLY the MCP tools it actually needs (can be empty [])
3. Order subtasks logically (dependencies first)

Respond in this EXACT JSON format (no markdown, no explanation):
{{
  "analysis": "Brief 1-sentence summary of what this task requires",
  "todos": [
    {{
      "task": "Clear description of subtask 1",
      "mcps": ["mcp-name-1", "mcp-name-2"],
      "reason": "Why these MCPs are needed"
    }},
    {{
      "task": "Clear description of subtask 2",
      "mcps": [],
      "reason": "No external tools needed"
    }}
  ],
  "estimated_iterations": 3
}}

IMPORTANT:
- Only assign MCPs that are ACTUALLY needed for each subtask
- Use empty [] if no external tools are required
- MCP names must match exactly from the list above
- Keep todos focused and actionable'''

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

    def _get_mcp_list(self) -> str:
        """Get formatted list of available MCPs for the prompt."""
        lines = []
        for server in get_all_servers():
            # Check if this MCP is actually available (has auth)
            from mcp_selector import _has_valid_auth
            has_auth, _ = _has_valid_auth(server)
            status = "[AVAILABLE]" if has_auth else "[NO AUTH]"
            lines.append(f"- {server.name}: {server.description} {status}")
        return "\n".join(lines)

    def plan(self, prompt: str) -> dict:
        """
        Analyze the task and create an execution plan.

        Returns:
            dict with analysis, todos (with MCP assignments), and metadata
        """
        import anthropic

        print(f"\n[wiggum] Analyzing task...")

        mcp_list = self._get_mcp_list()
        planning_prompt = self.PLANNING_PROMPT.format(
            prompt=prompt,
            mcp_list=mcp_list
        )

        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            messages=[{"role": "user", "content": planning_prompt}]
        )

        # Parse the JSON response
        response_text = response.content[0].text.strip()

        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        try:
            plan = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"[wiggum] Warning: Could not parse plan, using fallback")
            plan = {
                "analysis": "Single-task execution",
                "todos": [{"task": prompt, "mcps": [], "reason": "Fallback - no parsing"}],
                "estimated_iterations": 5
            }

        # Validate MCP names
        valid_mcps = {s.name for s in get_all_servers()}
        for todo in plan.get("todos", []):
            todo["mcps"] = [m for m in todo.get("mcps", []) if m in valid_mcps]

        # Display the plan
        self._display_plan(plan)

        return plan

    def _display_plan(self, plan: dict):
        """Display the execution plan to the user."""
        print(f"\n{'='*60}")
        print(f"  WIGGUM EXECUTION PLAN")
        print(f"{'='*60}")
        print(f"\nAnalysis: {plan.get('analysis', 'N/A')}")
        print(f"Estimated iterations: {plan.get('estimated_iterations', '?')}")
        print(f"\nTodos:")

        for i, todo in enumerate(plan.get("todos", []), 1):
            mcps = todo.get("mcps", [])
            mcp_str = ", ".join(mcps) if mcps else "(no external tools)"
            print(f"\n  {i}. {todo.get('task', 'Unknown task')}")
            print(f"     MCPs: {mcp_str}")
            if todo.get("reason"):
                print(f"     Reason: {todo.get('reason')}")

        print(f"\n{'='*60}\n")

    def get_mcps_for_plan(self, plan: dict) -> list[str]:
        """
        Get the union of all MCPs needed for the entire plan.
        Used when running in single-sandbox mode.
        """
        all_mcps = set()
        for todo in plan.get("todos", []):
            all_mcps.update(todo.get("mcps", []))
        return list(all_mcps)

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()


# ============================================================
# Ralph Wiggum Quotes - Easter eggs for tool use output
# ============================================================
RALPH_QUOTES = [
    {"category": "working", "quote": "I'm helping!"},
    {"category": "task_completion", "quote": "Me fail English? That's unpossible."},
    {"category": "thinking", "quote": "My cat's breath smells like cat food."},
    {"category": "working", "quote": "Hi, Super Nintendo Chalmers!"},
    {"category": "hard", "quote": "It tastes like... burning."},
    {"category": "task_completion", "quote": "I bent my Wookiee."},
    {"category": "thinking", "quote": "I'm learnding!"},
    {"category": "hard", "quote": "Miss Hoover, I glued my head to my shoulder."},
    {"category": "thinking", "quote": "What's a battle?"},
    {"category": "working", "quote": "I'm a unitard!"},
    {"category": "task_completion", "quote": "I'm a Star Wars!"},
    {"category": "thinking", "quote": "Sleep! That's where I'm a Viking!"},
    {"category": "hard", "quote": "Daddy, I'm scared. Too scared to even wet my pants."},
    {"category": "task_completion", "quote": "I found a moon rock in my nose!"},
    {"category": "thinking", "quote": "Go banana!"},
    {"category": "working", "quote": "When I grow up, I want to be a principal or a caterpillar."},
    {"category": "hard", "quote": "The doctor said I wouldn't have so many nose bleeds if I kept my finger outta there."},
    {"category": "thinking", "quote": "Lies are like stars, they always come out."},
    {"category": "task_completion", "quote": "I beat the smart kids!"},
    {"category": "working", "quote": "I'm a brick!"},
    {"category": "thinking", "quote": "So... do you like... stuff?"},
    {"category": "hard", "quote": "Why do people run from me?"},
    {"category": "task_completion", "quote": "Look, Daddy! A whale egg!"},
    {"category": "working", "quote": "I'm a furniture!"},
    {"category": "thinking", "quote": "I want to be a triangle."},
    {"category": "hard", "quote": "My sash says 'Idaho'!"},
    {"category": "working", "quote": "I'm Idaho!"},
    {"category": "task_completion", "quote": "And that's where I saw the leprechaun."},
    {"category": "thinking", "quote": "He tells me to burn things."},
    {"category": "hard", "quote": "This snowflake tastes like fish sticks."},
    {"category": "working", "quote": "I'm in danger."},
    {"category": "thinking", "quote": "If Mommy's purse didn't belong in the microwave, why did it fit?"},
    {"category": "task_completion", "quote": "I'm a pop sensation!"},
    {"category": "hard", "quote": "The pointy kitty took it!"},
    {"category": "thinking", "quote": "Slow down, Bart! My legs don't know how to be as long as yours."},
    {"category": "working", "quote": "I am a gulag."},
    {"category": "thinking", "quote": "Maybe we should kiss just to break the tension."},
    {"category": "hard", "quote": "My neck hurts and my ear hurts. I have two owies."},
    {"category": "working", "quote": "Principal Skinner is an old man who lives at the school."},
    {"category": "task_completion", "quote": "I finished my milk!"},
    {"category": "thinking", "quote": "Was I a good gator?"},
    {"category": "working", "quote": "Can you open my milk, Mommy?"},
    {"category": "hard", "quote": "This orange tastes like Grandpa!"},
    {"category": "thinking", "quote": "I like men now."},
    {"category": "task_completion", "quote": "We're a totem pole!"},
    {"category": "working", "quote": "I'm police chief!"},
    {"category": "hard", "quote": "It hurts when I utilize."},
    {"category": "thinking", "quote": "Does that mean you're not going to be my mommy?"},
    {"category": "task_completion", "quote": "I eated the purple berries."},
    {"category": "thinking", "quote": "Your eyes need diapers."},
    {"category": "working", "quote": "Pick me! I'm the only one with a tie!"},
    {"category": "hard", "quote": "I wet my arm pants."},
    {"category": "thinking", "quote": "I have five face holes."},
    {"category": "working", "quote": "This is my sandbox. I'm not allowed in the deep end."},
    {"category": "task_completion", "quote": "And when the doctor said I didn't have worms anymore, that was the happiest day of my life."},
    {"category": "thinking", "quote": "Oh boy, dirt! I'm a worm!"},
    {"category": "hard", "quote": "My knob tastes funny."},
    {"category": "working", "quote": "Look at me! I'm a heavy drinker!"},
    {"category": "thinking", "quote": "Fun toys are fun!"},
    {"category": "task_completion", "quote": "I made a special shiny!"},
    {"category": "hard", "quote": "I lost my map!"},
    {"category": "thinking", "quote": "Bushes are nice because they don't have prickers."},
    {"category": "working", "quote": "I'm digging to China!"},
    {"category": "hard", "quote": "Daddy, these rubber pants are hot."},
    {"category": "thinking", "quote": "My parents won't let me use scissors."},
    {"category": "task_completion", "quote": "I dressed myself."},
    {"category": "working", "quote": "I'm making a difference!"},
    {"category": "thinking", "quote": "Teacher told me to go sit in the corner and think about what I did."},
    {"category": "hard", "quote": "Trying is the first step towards failure."},
    {"category": "task_completion", "quote": "Look, I made a flag!"},
    {"category": "working", "quote": "I am the liz."},
    {"category": "thinking", "quote": "Is this a happy ending or a sad ending?"},
    {"category": "hard", "quote": "Everything I touch turns to ouch."},
    {"category": "working", "quote": "Working is when you sit and wait for the bell."},
    {"category": "task_completion", "quote": "I won! I won! ... What did I win?"},
    {"category": "thinking", "quote": "Are we there yet? ... How about now?"},
    {"category": "hard", "quote": "This game is hard. It makes my head hurts."},
    {"category": "working", "quote": "I'm an essential worker!"},
    {"category": "thinking", "quote": "Chicken necks?"},
    {"category": "task_completion", "quote": "I fixed it with gum!"},
    {"category": "hard", "quote": "I have a boo-boo on my brain."},
    {"category": "working", "quote": "Teamwork makes the dream work, but my dream is to be a Viking."},
    {"category": "thinking", "quote": "Why is the moon following me?"},
    {"category": "task_completion", "quote": "Look what I made! It's a disaster!"},
    {"category": "working", "quote": "I'm the boss of the sauce."},
    {"category": "hard", "quote": "Math makes me angry!"},
    {"category": "thinking", "quote": "If I close my eyes, you can't see me."},
    {"category": "working", "quote": "I'm assisting!"},
    {"category": "task_completion", "quote": "It's all done! Just like magic."},
    {"category": "thinking", "quote": "When the bell rings, I get to go home and eat dirt."},
    {"category": "hard", "quote": "I dropped my popsicle in the sand."},
    {"category": "working", "quote": "I'm supervising!"},
    {"category": "task_completion", "quote": "Done is better than perfect, that's what my shoe says."},
    {"category": "thinking", "quote": "My brain is taking a nap."},
    {"category": "working", "quote": "Look, I'm typing! Clickety-clack!"},
    {"category": "hard", "quote": "Adulting is hard, like chewing rocks."},
    {"category": "thinking", "quote": "I wonder if the clouds taste like marshmallows."},
]


# ============================================================
# AGENT CODE: Non-MCP version using claude-agent-sdk
# ============================================================
AGENT_CODE_SDK = '''
import asyncio
import os
import json
import random
import nest_asyncio

# Allow nested event loops (needed in Jupyter/E2B environment)
nest_asyncio.apply()

# Set API key in sandbox environment
os.environ["ANTHROPIC_API_KEY"] = "{api_key}"

from claude_agent_sdk import ClaudeAgentOptions, query

# ============================================================
# ANSI Color Codes for pretty terminal output
# ============================================================
class C:
    RESET = "\\033[0m"
    BOLD = "\\033[1m"
    DIM = "\\033[2m"
    # Colors
    RED = "\\033[91m"
    GREEN = "\\033[92m"
    YELLOW = "\\033[93m"
    BLUE = "\\033[94m"
    MAGENTA = "\\033[95m"
    CYAN = "\\033[96m"
    WHITE = "\\033[97m"
    # Backgrounds
    BG_YELLOW = "\\033[43m"
    BG_BLUE = "\\033[44m"

# Ralph Wiggum quotes for easter eggs
RALPH_QUOTES = {ralph_quotes_json}

def ralph_says(category="working"):
    \"\"\"Get a random Ralph quote for the given category.\"\"\"
    quotes = [q["quote"] for q in RALPH_QUOTES if q["category"] == category]
    if not quotes:
        quotes = [q["quote"] for q in RALPH_QUOTES]
    return random.choice(quotes)

def print_ralph(category="working"):
    \"\"\"Print a Ralph Wiggum quote with formatting.\"\"\"
    quote = ralph_says(category)
    print(f"{{C.YELLOW}}{{C.BOLD}}    [Ralph]{{C.RESET}} {{C.YELLOW}}{{quote}}{{C.RESET}}")

def print_tool(name, input_str):
    \"\"\"Print tool use with colors.\"\"\"
    print(f"{{C.CYAN}}{{C.BOLD}}[tool]{{C.RESET}} {{C.CYAN}}{{name}}{{C.RESET}}{{C.DIM}}: {{input_str[:180]}}{{C.RESET}}")
    # 30% chance to show a Ralph quote
    if random.random() < 0.3:
        print_ralph("working")

def print_tool_result(content):
    \"\"\"Print tool result with colors.\"\"\"
    print(f"{{C.GREEN}}[result]{{C.RESET}} {{C.DIM}}{{str(content)[:180]}}...{{C.RESET}}")

def print_error(msg):
    \"\"\"Print error with colors.\"\"\"
    print(f"{{C.RED}}{{C.BOLD}}[error]{{C.RESET}} {{C.RED}}{{msg}}{{C.RESET}}")
    if random.random() < 0.5:
        print_ralph("hard")

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

    # Show a thinking quote at start
    print_ralph("thinking")

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
    tool_count = 0
    async for message in query(
        prompt=full_prompt,
        options=options
    ):
        if hasattr(message, "result"):
            result_text = message.result
            # result is captured for completion check, already printed via content blocks
        elif hasattr(message, "content"):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)
                elif hasattr(block, "type"):
                    # Handle tool use blocks
                    if block.type == "tool_use":
                        tool_name = getattr(block, "name", "unknown")
                        tool_input = getattr(block, "input", {{}})
                        input_str = json.dumps(tool_input) if isinstance(tool_input, dict) else str(tool_input)
                        print_tool(tool_name, input_str)
                        tool_count += 1
                    elif block.type == "tool_result":
                        content = getattr(block, "content", "")
                        if isinstance(content, list):
                            content = " ".join(str(c) for c in content[:2])
                        print_tool_result(content)

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
        print_error(f"could not save state: {{e}}")

    # Check for completion
    if completion_promise in result_text:
        print(f"\\n{{C.GREEN}}{{C.BOLD}}[ralph]{{C.RESET}} {{C.GREEN}}completion signal detected{{C.RESET}}")
        print_ralph("task_completion")

asyncio.run(run_agent())
'''


# ============================================================
# AGENT CODE: MCP-enabled version with FULL LOOP INSIDE SANDBOX
# The entire ralph-wiggum loop runs inside the sandbox
# ============================================================
AGENT_CODE_MCP = '''
import os
import json
import random
import time

# Set API key in sandbox environment
os.environ["ANTHROPIC_API_KEY"] = "{api_key}"

import anthropic

# ============================================================
# ANSI Color Codes for pretty terminal output
# ============================================================
class C:
    RESET = "\\033[0m"
    BOLD = "\\033[1m"
    DIM = "\\033[2m"
    RED = "\\033[91m"
    GREEN = "\\033[92m"
    YELLOW = "\\033[93m"
    BLUE = "\\033[94m"
    MAGENTA = "\\033[95m"
    CYAN = "\\033[96m"
    WHITE = "\\033[97m"

# Ralph Wiggum quotes for easter eggs
RALPH_QUOTES = {ralph_quotes_json}

def ralph_says(category="working"):
    quotes = [q["quote"] for q in RALPH_QUOTES if q["category"] == category]
    if not quotes:
        quotes = [q["quote"] for q in RALPH_QUOTES]
    return random.choice(quotes)

def print_ralph(category="working"):
    quote = ralph_says(category)
    print(f"{{C.YELLOW}}{{C.BOLD}}    [Ralph]{{C.RESET}} {{C.YELLOW}}{{quote}}{{C.RESET}}")

def print_iteration(current, max_iter):
    bar = "=" * 60
    print(f"\\n{{C.CYAN}}{{C.BOLD}}{{bar}}{{C.RESET}}")
    print(f"{{C.CYAN}}{{C.BOLD}}  RALPH LOOP - ITERATION {{current}}/{{max_iter}}{{C.RESET}}")
    print(f"{{C.CYAN}}{{C.BOLD}}{{bar}}{{C.RESET}}\\n")

def print_tool(name, input_str, is_mcp=False, server=None):
    if is_mcp and server:
        print(f"{{C.MAGENTA}}{{C.BOLD}}[mcp]{{C.RESET}} {{C.MAGENTA}}{{server}}/{{name}}{{C.RESET}}{{C.DIM}}: {{input_str[:160]}}{{C.RESET}}")
    else:
        print(f"{{C.CYAN}}{{C.BOLD}}[tool]{{C.RESET}} {{C.CYAN}}{{name}}{{C.RESET}}{{C.DIM}}: {{input_str[:180]}}{{C.RESET}}")
    if random.random() < 0.3:
        print_ralph("working")

def print_tool_result(content, is_mcp=False):
    prefix = "[mcp-result]" if is_mcp else "[result]"
    color = C.BLUE if is_mcp else C.GREEN
    print(f"{{color}}{{prefix}}{{C.RESET}} {{C.DIM}}{{str(content)[:180]}}...{{C.RESET}}")

def print_error(msg):
    print(f"{{C.RED}}{{C.BOLD}}[error]{{C.RESET}} {{C.RED}}{{msg}}{{C.RESET}}")
    if random.random() < 0.5:
        print_ralph("hard")

# ============================================================
# STATE MANAGEMENT (stop-hook pattern inside sandbox)
# ============================================================
STATE_FILE = "/home/user/ralph_state.json"
WORKSPACE = "/home/user/workspace"

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {{"iteration": 0, "history": [], "status": "running"}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def get_previous_context(state):
    if not state.get("history"):
        return ""
    context = "\\n\\n--- Previous Iteration Results ---\\n"
    for i, h in enumerate(state["history"][-3:], 1):
        context += f"\\nIteration {{i}}:\\n{{h[:800]}}...\\n"
    return context

# ============================================================
# LOCAL TOOLS - File operations and code execution
# ============================================================
LOCAL_TOOLS = [
    {{
        "name": "write_file",
        "description": "Write content to a file in the workspace. Creates parent directories if needed.",
        "input_schema": {{
            "type": "object",
            "properties": {{
                "path": {{"type": "string", "description": "File path relative to workspace (e.g., 'output.txt' or 'data/results.json')"}},
                "content": {{"type": "string", "description": "Content to write to the file"}}
            }},
            "required": ["path", "content"]
        }}
    }},
    {{
        "name": "read_file",
        "description": "Read content from a file in the workspace.",
        "input_schema": {{
            "type": "object",
            "properties": {{
                "path": {{"type": "string", "description": "File path relative to workspace"}}
            }},
            "required": ["path"]
        }}
    }},
    {{
        "name": "list_files",
        "description": "List all files in the workspace directory.",
        "input_schema": {{
            "type": "object",
            "properties": {{}},
            "required": []
        }}
    }},
    {{
        "name": "execute_python",
        "description": "Execute Python code and return the output. Use for data processing, calculations, or generating content.",
        "input_schema": {{
            "type": "object",
            "properties": {{
                "code": {{"type": "string", "description": "Python code to execute"}}
            }},
            "required": ["code"]
        }}
    }}
]

def handle_local_tool(name, input_data):
    \"\"\"Execute a local tool and return the result.\"\"\"
    try:
        if name == "write_file":
            path = os.path.join(WORKSPACE, input_data["path"])
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else WORKSPACE, exist_ok=True)
            with open(path, "w") as f:
                f.write(input_data["content"])
            return f"Successfully wrote {{len(input_data['content'])}} characters to {{input_data['path']}}"

        elif name == "read_file":
            path = os.path.join(WORKSPACE, input_data["path"])
            if os.path.exists(path):
                with open(path, "r") as f:
                    content = f.read()
                return content[:5000] if len(content) > 5000 else content
            else:
                return f"Error: File not found: {{input_data['path']}}"

        elif name == "list_files":
            files = []
            for root, dirs, filenames in os.walk(WORKSPACE):
                for fn in filenames:
                    rel_path = os.path.relpath(os.path.join(root, fn), WORKSPACE)
                    files.append(rel_path)
            return "\\n".join(files) if files else "No files in workspace"

        elif name == "execute_python":
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                exec(input_data["code"], {{"__builtins__": __builtins__, "os": os, "json": json}})
                output = sys.stdout.getvalue()
            except Exception as e:
                output = f"Error: {{str(e)}}"
            finally:
                sys.stdout = old_stdout
            return output if output else "Code executed successfully (no output)"

        else:
            return f"Unknown tool: {{name}}"
    except Exception as e:
        return f"Tool error: {{str(e)}}"

# ============================================================
# SINGLE ITERATION - One pass through Claude with MCP + Local tools
# ============================================================
def run_single_iteration(prompt, iteration, max_iterations, completion_promise, mcp_servers, mcp_toolsets, previous_context):
    print_ralph("thinking")

    full_prompt = f"""{{prompt}}

ITERATION: {{iteration}} / {{max_iterations}}
{{previous_context}}

IMPORTANT:
- You are in a Ralph Wiggum loop - working autonomously until the task is complete
- Output "{{completion_promise}}" when you have fully completed the task
- WORKSPACE: You are in {{WORKSPACE}} - save ALL outputs here (they will be downloaded)
- You have {{max_iterations - iteration}} iterations remaining
- Do not use emojis or special characters in your output - keep it plain text
- You have access to MCP tools from external services AND local tools for file operations
- USE write_file tool to create files, read_file to read them, list_files to see workspace
- READ your previous work before continuing - check files you created
"""

    client = anthropic.Anthropic()
    messages = [{{"role": "user", "content": full_prompt}}]
    result_text = ""
    max_turns = 25
    turn = 0

    # Combine local tools with MCP toolsets
    all_tools = LOCAL_TOOLS.copy()
    if mcp_toolsets:
        all_tools.extend(mcp_toolsets)

    while turn < max_turns:
        turn += 1
        try:
            request_params = {{
                "model": "claude-sonnet-4-5",
                "max_tokens": 16000,
                "messages": messages,
                "tools": all_tools,
            }}

            if mcp_servers:
                request_params["mcp_servers"] = mcp_servers
                response = client.beta.messages.create(
                    **request_params,
                    betas=["mcp-client-2025-11-20"]
                )
            else:
                response = client.messages.create(**request_params)

            assistant_content = []
            tool_results = []
            has_tool_use = False

            for block in response.content:
                if block.type == "text":
                    print(block.text)
                    result_text += block.text
                    assistant_content.append({{"type": "text", "text": block.text}})

                elif block.type == "tool_use":
                    # Local tool - we handle it ourselves
                    has_tool_use = True
                    assistant_content.append({{
                        "type": "tool_use", "id": block.id,
                        "name": block.name, "input": block.input
                    }})
                    print_tool(block.name, json.dumps(block.input))

                    # Execute the local tool
                    tool_result = handle_local_tool(block.name, block.input)
                    print_tool_result(tool_result, is_mcp=False)
                    tool_results.append({{
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result
                    }})

                elif block.type == "mcp_tool_use":
                    # MCP tool - handled by Anthropic API
                    has_tool_use = True
                    assistant_content.append({{
                        "type": "mcp_tool_use", "id": block.id,
                        "name": block.name, "server_name": block.server_name,
                        "input": block.input
                    }})
                    print_tool(block.name, json.dumps(block.input), is_mcp=True, server=block.server_name)

                elif block.type == "mcp_tool_result":
                    result_content = ""
                    if hasattr(block, "content"):
                        for item in block.content:
                            if hasattr(item, "text"):
                                result_content = item.text[:500]
                    print_tool_result(result_content, is_mcp=True)

            messages.append({{"role": "assistant", "content": assistant_content}})

            # Add local tool results if any
            if tool_results:
                messages.append({{"role": "user", "content": tool_results}})

            if response.stop_reason == "end_turn" or not has_tool_use:
                break

            if response.stop_reason == "tool_use":
                messages.append({{
                    "role": "user",
                    "content": "Continue with the task. Process tool results and continue working."
                }})

        except Exception as e:
            print_error(f"API error: {{e}}")
            break

    return result_text

# ============================================================
# MAIN RALPH LOOP - Runs entirely inside sandbox
# This is the stop-hook pattern: iterate until complete
# ============================================================
def ralph_loop():
    prompt = """{prompt}"""
    max_iterations = {max_iterations}
    completion_promise = "{completion_promise}"
    mcp_servers = {mcp_servers_json}
    mcp_toolsets = {mcp_toolsets_json}

    os.makedirs(WORKSPACE, exist_ok=True)
    os.chdir(WORKSPACE)

    state = load_state()

    print(f"{{C.GREEN}}{{C.BOLD}}[ralph]{{C.RESET}} {{C.GREEN}}Starting autonomous loop{{C.RESET}}")
    print(f"{{C.DIM}}  Max iterations: {{max_iterations}}{{C.RESET}}")
    print(f"{{C.DIM}}  Completion signal: {{completion_promise}}{{C.RESET}}")
    print(f"{{C.DIM}}  MCP servers: {{len(mcp_servers)}}{{C.RESET}}")

    # ============================================================
    # THE LOOP - same pattern as ralph-wiggum stop-hook
    # ============================================================
    while state["iteration"] < max_iterations:
        state["iteration"] += 1
        current = state["iteration"]

        print_iteration(current, max_iterations)

        previous_context = get_previous_context(state)

        # Run one iteration
        result_text = run_single_iteration(
            prompt, current, max_iterations, completion_promise,
            mcp_servers, mcp_toolsets, previous_context
        )

        # Save iteration result to history
        state["history"].append(result_text[:2000] if result_text else "No output")
        save_state(state)

        # ============================================================
        # STOP-HOOK CHECK: Did we hit completion promise?
        # ============================================================
        if completion_promise in result_text:
            state["status"] = "completed"
            save_state(state)
            print(f"\\n{{C.GREEN}}{{C.BOLD}}[ralph]{{C.RESET}} {{C.GREEN}}Completion signal detected!{{C.RESET}}")
            print_ralph("task_completion")
            print(f"\\n{{C.GREEN}}Task completed in {{current}} iteration(s){{C.RESET}}")
            return "completed"

        # Not complete - continue loop (stop-hook re-feed behavior)
        print(f"\\n{{C.YELLOW}}[ralph]{{C.RESET}} {{C.DIM}}Iteration {{current}} complete, continuing...{{C.RESET}}")
        print_ralph("working")
        time.sleep(1)  # Brief pause between iterations

    # Max iterations reached
    state["status"] = "max_iterations"
    save_state(state)
    print(f"\\n{{C.YELLOW}}{{C.BOLD}}[ralph]{{C.RESET}} {{C.YELLOW}}Max iterations ({{max_iterations}}) reached{{C.RESET}}")
    print_ralph("hard")
    return "max_iterations"

# Run the full loop
result = ralph_loop()
print(f"\\n{{C.CYAN}}[ralph] Final status: {{result}}{{C.RESET}}")
'''


class RalphLoop:
    """
    Ralph Wiggum Loop: Self-referential agent iteration in E2B sandbox.

    Supports MCP (Model Context Protocol) connectors for external tool access.
    """

    # Patterns for environment variables to pass into sandbox
    CREDENTIAL_PATTERNS = [
        "_API_KEY",
        "_API_SECRET",
        "_TOKEN",
        "_SECRET",
        "_PASSWORD",
        "_CREDENTIAL",
        "API_KEY",
        "AUTH_",
        "OPENAI_",
        "ANTHROPIC_",
        "AWS_",
        "GOOGLE_",
        "AZURE_",
        "GITHUB_",
        "STRIPE_",
        "TWILIO_",
        "SENDGRID_",
        "SLACK_",
        "DISCORD_",
        "NOTION_",
        "LINEAR_",
        "JIRA_",
        "JULES_",
        "MCP_",
        "E2B_",
        "SUPABASE_",
        "FIREBASE_",
        "MONGODB_",
        "POSTGRES_",
        "REDIS_",
        "DATABASE_",
        "DB_",
    ]

    def __init__(
        self,
        prompt: str,
        max_iterations: int = 10,
        completion_promise: str = "COMPLETE",
        timeout: int = 600,
        output_dir: str | None = None,
        mcp_mode: str = "auto",  # "auto", "none", "plan", or comma-separated server names
        plan: dict | None = None,  # Pre-computed Wiggum plan
    ):
        self.prompt = prompt
        self.max_iterations = max_iterations
        self.completion_promise = completion_promise
        self.timeout = timeout
        self.output_dir = output_dir or os.path.join(os.getcwd(), "ralph_output")
        self.plan = plan  # Wiggum's execution plan
        self.current_iteration = 0
        self.sandbox = None
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.mcp_mode = mcp_mode
        self.mcp_selection: MCPSelection | None = None
        self.credentials: dict[str, str] = {}

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")

        # Collect all credentials from environment
        self._collect_credentials()

        # Select MCP servers based on mode
        self._configure_mcp()

    def _collect_credentials(self):
        """Collect all credentials from environment to pass into sandbox."""
        for key, value in os.environ.items():
            # Check if this looks like a credential
            if any(pattern in key.upper() for pattern in self.CREDENTIAL_PATTERNS):
                if value and value.strip():  # Only include non-empty values
                    self.credentials[key] = value

        # Log what we found (without revealing values)
        if self.credentials:
            cred_names = list(self.credentials.keys())
            print(f"[ralph] credentials found: {', '.join(cred_names)}")

    def _inject_credentials(self):
        """Inject collected credentials into the sandbox environment."""
        if not self.credentials:
            return

        # Build code to set all environment variables
        env_code = "import os\n"
        for key, value in self.credentials.items():
            # Escape the value for safe insertion
            escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
            env_code += f'os.environ["{key}"] = "{escaped_value}"\n'
        env_code += 'print(f"[sandbox] {len(os.environ)} env vars loaded")\n'

        result = self.sandbox.run_code(env_code)
        if result.logs.stdout:
            print("".join(result.logs.stdout).strip())
        if result.error:
            print(f"[ralph] warning: credential injection error: {result.error}")

    def _configure_mcp(self):
        """Configure MCP servers based on mode setting."""
        if self.mcp_mode == "none":
            self.mcp_selection = None
            return

        if self.mcp_mode == "plan" and self.plan:
            # Use MCPs from Wiggum's plan
            planner = WiggumPlanner()
            plan_mcps = planner.get_mcps_for_plan(self.plan)
            if plan_mcps:
                self.mcp_selection = select_mcp_servers(
                    self.prompt,
                    explicit_servers=plan_mcps,
                    allowed_auth_types=["open", "api_key", "oauth"],
                )
            else:
                self.mcp_selection = None
        elif self.mcp_mode == "auto":
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

        # Inject all credentials into sandbox environment
        self._inject_credentials()

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

    def _run_loop_in_sandbox(self) -> str:
        """
        Run the entire Ralph loop inside the sandbox.
        The loop logic is now in AGENT_CODE_MCP - we just launch once.

        Returns:
            Final output from the sandbox
        """
        # Escape prompt for string formatting
        escaped_prompt = (
            self.prompt.replace('"""', '\\"\\"\\"').replace("{", "{{").replace("}", "}}")
        )

        # Serialize Ralph quotes for injection into sandbox
        ralph_quotes_json = json.dumps(RALPH_QUOTES)

        if self._use_mcp_mode():
            # Use MCP-enabled agent code with full loop inside
            agent_code = AGENT_CODE_MCP.format(
                api_key=self.api_key,
                prompt=escaped_prompt,
                max_iterations=self.max_iterations,
                completion_promise=self.completion_promise,
                mcp_servers_json=json.dumps(self.mcp_selection.servers),
                mcp_toolsets_json=json.dumps(self.mcp_selection.toolsets),
                ralph_quotes_json=ralph_quotes_json,
            )
        else:
            # Use SDK-based agent code (no MCP) - still uses old single-iteration
            # TODO: Update AGENT_CODE_SDK to also have full loop
            agent_code = AGENT_CODE_SDK.format(
                api_key=self.api_key,
                prompt=escaped_prompt,
                iteration=1,
                max_iterations=self.max_iterations,
                completion_promise=self.completion_promise,
                ralph_quotes_json=ralph_quotes_json,
            )

        # Run the full loop inside the sandbox - this blocks until complete
        result = self.sandbox.run_code(agent_code)

        output = ""
        if result.logs.stdout:
            output = "".join(result.logs.stdout)
            print(output)

        if result.logs.stderr:
            stderr = "".join(result.logs.stderr)
            if stderr.strip():
                print(f"[ralph] stderr: {stderr}")

        if result.error:
            print(f"[ralph] error: {result.error.name}: {result.error.value}")

        return output

    def run(self) -> dict:
        """
        Run the Ralph Wiggum loop.

        The entire loop now runs INSIDE the sandbox (stop-hook pattern).
        We launch once and wait for completion.

        Returns:
            dict with status, iterations, output history, and downloaded files
        """
        print("[ralph] launching autonomous sandbox agent")
        print(f"[ralph] prompt: {self.prompt[:80]}...")
        print(f"[ralph] max_iterations: {self.max_iterations}")
        print(f"[ralph] completion_signal: {self.completion_promise}")
        print(f"[ralph] mode: {'MCP' if self._use_mcp_mode() else 'SDK'}")
        if self._use_mcp_mode():
            print(f"[ralph] MCP servers: {', '.join(self.mcp_selection.selected_names)}")

        downloaded_files = []
        status = "unknown"
        output = ""

        try:
            self._create_sandbox()

            # Run the ENTIRE loop inside the sandbox
            # This blocks until the loop completes (or max iterations)
            output = self._run_loop_in_sandbox()

            # Determine status from output
            if "completed" in output.lower() and self.completion_promise in output:
                status = "completed"
            elif "max_iterations" in output.lower():
                status = "max_iterations_reached"
            else:
                status = "completed" if self.completion_promise in output else "unknown"

            # Download all workspace files
            if self.sandbox:
                print("\n[ralph] retrieving workspace files...")
                downloaded_files = self._download_workspace()

        except Exception as e:
            print(f"[ralph] error: {e}")
            status = "error"

        finally:
            if self.sandbox:
                print(f"[ralph] cleanup: {self.sandbox.sandbox_id}")
                self.sandbox.kill()

        return {
            "status": status,
            "iterations": self.max_iterations,  # Loop ran inside, we don't track externally
            "max_iterations": self.max_iterations,
            "output": output[:5000],
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
    use_wiggum: bool = True,
) -> dict:
    """
    Launch a Ralph Wiggum loop with optional Wiggum planning phase.

    Args:
        prompt: The task for the agent to work on
        max_iterations: Maximum iterations before stopping (default 10)
        completion_promise: Text that signals task completion (default "COMPLETE")
        timeout: Sandbox timeout in seconds (default 10 minutes)
        output_dir: Local directory to save workspace files (default: ./ralph_output)
        mcp: MCP mode - "auto", "none", "plan" (use Wiggum's assignments), or
             comma-separated server names like "exa-search,aws-knowledge"
        use_wiggum: If True, run Wiggum planning phase first (default True)

    Returns:
        dict with status, iterations, output history, downloaded files, and plan
    """
    plan = None

    # Run Wiggum planning phase if enabled
    if use_wiggum:
        planner = WiggumPlanner()
        plan = planner.plan(prompt)

        # Use plan-based MCP selection
        mcp = "plan"

        # Update max_iterations from plan if provided
        if plan.get("estimated_iterations"):
            suggested = plan["estimated_iterations"]
            if suggested > max_iterations:
                print(f"[wiggum] Adjusting max_iterations: {max_iterations} -> {suggested}")
                max_iterations = suggested

    # Build enhanced prompt with Wiggum's todos
    enhanced_prompt = prompt
    if plan and plan.get("todos"):
        todos_text = "\n".join(
            f"  {i}. {todo['task']}" for i, todo in enumerate(plan["todos"], 1)
        )
        enhanced_prompt = f"""{prompt}

WIGGUM'S EXECUTION PLAN:
{todos_text}

Work through these todos in order. Output {completion_promise} when ALL todos are complete."""

    ralph = RalphLoop(
        prompt=enhanced_prompt,
        max_iterations=max_iterations,
        completion_promise=completion_promise,
        timeout=timeout,
        output_dir=output_dir,
        mcp_mode=mcp,
        plan=plan,
    )

    result = ralph.run()
    result["plan"] = plan
    return result


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
