import asyncio
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

# Load environment variables from .env
load_dotenv()

# Global sandbox instance
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
    {"code": str}
)
async def execute_python(args: dict[str, Any]) -> dict[str, Any]:
    """Execute Python code in E2B sandbox."""
    code: str = args["code"]
    try:
        sbx = await get_or_create_sandbox()
        execution = await sbx.run_code(code)

        outputs = []
        if execution.logs.stdout:
            outputs.append(f"stdout:\n{execution.logs.stdout}")
        if execution.logs.stderr:
            outputs.append(f"stderr:\n{execution.logs.stderr}")
        if execution.error:
            outputs.append(f"Error: {execution.error.name}: {execution.error.value}")

        for result in execution.results:
            if hasattr(result, 'text') and result.text:
                outputs.append(f"Result: {result.text}")
            if hasattr(result, 'png') and result.png:
                outputs.append("[Chart generated]")

        return {
            "content": [{
                "type": "text",
                "text": "\n\n".join(outputs) if outputs else "Code executed successfully (no output)"
            }]
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Execution failed: {str(e)}"}]
        }

# Create the MCP server with the E2B tool
e2b_server = create_sdk_mcp_server(
    name="e2b-sandbox",
    version="1.0.0",
    tools=[execute_python]
)

async def main() -> None:
    print("Starting Claude + E2B Agent...")

    prompt = "Calculate the first 10 prime numbers using Python and explain the result."

    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                mcp_servers={"e2b-sandbox": e2b_server},
                allowed_tools=["mcp__e2b-sandbox__execute_python"]
            )
        ):
            if hasattr(message, "result"):
                print("\n--- Agent Result ---\n")
                print(message.result)
    finally:
        if sandbox:
            await sandbox.close()

if __name__ == "__main__":
    asyncio.run(main())
