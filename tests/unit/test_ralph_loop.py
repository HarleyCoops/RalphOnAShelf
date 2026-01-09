from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("e2b_code_interpreter")

import main


class FakeLogs:
    def __init__(self, stdout: list[str] | None = None, stderr: list[str] | None = None) -> None:
        self.stdout = stdout or []
        self.stderr = stderr or []


class FakeResult:
    def __init__(
        self,
        stdout: list[str] | None = None,
        stderr: list[str] | None = None,
        error: Any | None = None,
    ) -> None:
        self.logs = FakeLogs(stdout=stdout, stderr=stderr)
        self.error = error


class FakeFiles:
    def list(self, path: str) -> list[Any]:
        return []

    def read(self, path: str) -> bytes:
        return b""


class FakeSandbox:
    last_instance: "FakeSandbox | None" = None

    def __init__(self, **kwargs: Any) -> None:
        self.timeout = kwargs.get("timeout", 0)
        self.sandbox_id = "fake-sandbox"
        self.files = FakeFiles()
        self.killed = False
        FakeSandbox.last_instance = self

    @classmethod
    def create(cls, **kwargs: Any) -> "FakeSandbox":
        return cls(**kwargs)

    def run_code(self, code: str) -> FakeResult:
        if "pip" in code:
            return FakeResult(stdout=["done\n"])
        return FakeResult(stdout=["iteration output\n", "COMPLETE\n"])

    def kill(self) -> None:
        self.killed = True


def test_ralph_loop_completes_first_iteration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(main, "Sandbox", FakeSandbox)

    result = main.launch_ralph(
        prompt="Do the thing. Output COMPLETE when done.",
        max_iterations=3,
        completion_promise="COMPLETE",
        timeout=5,
    )

    assert result["status"] == "completed"
    assert result["iterations"] == 1
    assert FakeSandbox.last_instance is not None
    assert FakeSandbox.last_instance.killed is True
