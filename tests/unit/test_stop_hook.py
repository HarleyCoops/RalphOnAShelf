from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = ROOT / ".claude-plugins" / "ralph-on-shelf" / "hooks" / "stop.py"

spec = importlib.util.spec_from_file_location("ros_stop_hook", HOOK_PATH)
assert spec and spec.loader
stop_hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stop_hook)


def _write_state(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state))


def test_stop_hook_no_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_file = tmp_path / ".ros-state.json"
    monkeypatch.setattr(stop_hook, "STATE_FILE", state_file)

    with pytest.raises(SystemExit) as exc:
        stop_hook.main()

    assert exc.value.code == 0


def test_stop_hook_max_iterations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_file = tmp_path / ".ros-state.json"
    monkeypatch.setattr(stop_hook, "STATE_FILE", state_file)

    _write_state(
        state_file,
        {
            "active": True,
            "current_iteration": 2,
            "max_iterations": 2,
            "status": "running",
        },
    )

    with pytest.raises(SystemExit) as exc:
        stop_hook.main()

    assert exc.value.code == 0
    saved = json.loads(state_file.read_text())
    assert saved["active"] is False
    assert saved["status"] == "max_iterations_reached"
    assert isinstance(saved.get("ended_at"), str)


def test_stop_hook_completed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_file = tmp_path / ".ros-state.json"
    monkeypatch.setattr(stop_hook, "STATE_FILE", state_file)

    _write_state(
        state_file,
        {
            "active": True,
            "current_iteration": 3,
            "max_iterations": 10,
            "status": "completed",
        },
    )

    with pytest.raises(SystemExit) as exc:
        stop_hook.main()

    assert exc.value.code == 0
    saved = json.loads(state_file.read_text())
    assert saved["active"] is False
    assert saved["status"] == "completed"
    assert isinstance(saved.get("ended_at"), str)


def test_stop_hook_continue(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_file = tmp_path / ".ros-state.json"
    monkeypatch.setattr(stop_hook, "STATE_FILE", state_file)

    _write_state(
        state_file,
        {
            "active": True,
            "current_iteration": 1,
            "max_iterations": 3,
            "status": "running",
            "prompt": "Do work",
            "completion_promise": "COMPLETE",
        },
    )

    with pytest.raises(SystemExit) as exc:
        stop_hook.main()

    assert exc.value.code == 1
    saved = json.loads(state_file.read_text())
    assert saved["active"] is True
    assert saved["current_iteration"] == 2
