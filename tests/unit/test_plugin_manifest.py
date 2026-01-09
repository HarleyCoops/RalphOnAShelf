from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = ROOT / ".claude-plugins" / "ralph-on-shelf"
PLUGIN_JSON = PLUGIN_ROOT / "plugin.json"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def test_plugin_manifest_fields() -> None:
    data = _load_json(PLUGIN_JSON)

    assert isinstance(data.get("name"), str) and data["name"]
    assert isinstance(data.get("version"), str) and SEMVER_RE.match(data["version"])
    assert isinstance(data.get("description"), str) and data["description"]
    assert isinstance(data.get("license"), str) and data["license"]

    author = data.get("author")
    assert isinstance(author, dict)
    assert isinstance(author.get("name"), str) and author["name"]

    repository = data.get("repository")
    assert isinstance(repository, dict)
    assert repository.get("type") == "git"
    assert isinstance(repository.get("url"), str) and repository["url"].startswith("https://")

    assert isinstance(data.get("source"), str) and data["source"].startswith("https://")


def test_plugin_paths_exist() -> None:
    data = _load_json(PLUGIN_JSON)

    for key in ("commands", "hooks", "agents"):
        rel_path = data.get(key)
        assert isinstance(rel_path, str) and rel_path
        target = (PLUGIN_ROOT / rel_path).resolve()
        assert target.exists() and target.is_dir()

    assert (PLUGIN_ROOT / "README.md").exists()

    command_files = list((PLUGIN_ROOT / "commands").glob("*.md"))
    assert command_files

    hook_files = list((PLUGIN_ROOT / "hooks").glob("*.py"))
    assert hook_files

    agent_files = list((PLUGIN_ROOT / "agents").glob("*.md"))
    assert agent_files
