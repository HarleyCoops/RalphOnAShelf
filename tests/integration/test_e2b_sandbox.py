"""Integration test that verifies E2B sandbox connectivity and execution."""
from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

pytestmark = pytest.mark.integration


def test_e2b_sandbox_exec() -> None:
    load_dotenv()
    if not os.getenv("E2B_API_KEY"):
        pytest.skip("E2B_API_KEY not set")

    sbx: Sandbox | None = None
    try:
        sbx = Sandbox()
        result = sbx.run_code('print("Hello from E2B sandbox!")')
        stdout = "".join(result.logs.stdout or [])

        assert "Hello from E2B sandbox!" in stdout
        assert result.error is None

        result = sbx.run_code(
            "import sys\n"
            "print(f\"Python version: {sys.version}\")\n"
            "primes = [n for n in range(2, 50) if all(n % i != 0 for i in range(2, int(n**0.5)+1))]\n"
            "print(f\"Primes under 50: {primes}\")\n"
        )
        stdout = "".join(result.logs.stdout or [])

        assert "Python version:" in stdout
        assert "Primes under 50:" in stdout
        assert result.error is None
    finally:
        if sbx is not None:
            sbx.kill()
