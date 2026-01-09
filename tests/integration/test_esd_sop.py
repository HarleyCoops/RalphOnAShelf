from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("dotenv")
pytest.importorskip("e2b_code_interpreter")

from dotenv import load_dotenv

from main import launch_ralph

pytestmark = pytest.mark.integration

PROMPT = """You are a Warehouse Manager responsible for developing processes and procedures for the team members to utilize as guidance for their daily activities and tasks.

TASK: Create a standard operating procedure (SOP) in Word format (.docx) for the handling and storage of ESD-sensitive items.

REQUIREMENTS:
1. Reference standard: IPC-A-610G Acceptability of Electronic Assemblies (https://www.electronics.org/TOC/IPC-A-610G.pdf).
2. Length: No more than 5 pages.
3. Content: Cover proper handling, storage, and training requirements for the warehouse team.
4. Format: Professional SOP layout.
5. SAVE THE FINAL FILE TO: output/ESD_Handling_SOP.docx

You have 'python-docx' installed in the environment. Use it to create the document.
Create the 'output/' directory first if it doesn't exist.

Output COMPLETE when the file is saved and verified.
"""


def test_esd_sop_docx_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    load_dotenv()
    missing = [
        name for name in ("ANTHROPIC_API_KEY", "E2B_API_KEY") if not os.getenv(name)
    ]
    if missing:
        pytest.skip(f"Missing env vars: {', '.join(missing)}")

    monkeypatch.chdir(tmp_path)

    result = launch_ralph(
        prompt=PROMPT,
        max_iterations=10,
        completion_promise="COMPLETE",
        timeout=1200,
    )

    assert result["status"] == "completed", (
        "Ralph did not complete in "
        f"{result['iterations']}/{result['max_iterations']} iterations."
    )

    output_path = tmp_path / "output" / "ESD_Handling_SOP.docx"
    assert output_path.exists()
    assert output_path.stat().st_size > 0
