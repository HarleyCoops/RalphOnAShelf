from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def test_marketplace_manifest_shape() -> None:
    marketplace_path = ROOT / "marketplace.json"
    data = _load_json(marketplace_path)

    assert isinstance(data.get("name"), str) and data["name"]
    owner = data.get("owner")
    assert isinstance(owner, dict)
    assert isinstance(owner.get("name"), str) and owner["name"]

    plugins = data.get("plugins")
    assert isinstance(plugins, list) and plugins

    for plugin in plugins:
        assert isinstance(plugin.get("name"), str) and plugin["name"]
        assert isinstance(plugin.get("description"), str) and plugin["description"]
        assert isinstance(plugin.get("author"), str) and plugin["author"]
        assert isinstance(plugin.get("source"), str) and plugin["source"]
        assert isinstance(plugin.get("version"), str) and plugin["version"]
        assert SEMVER_RE.match(plugin["version"])

        source = plugin["source"]
        if source.startswith("."):
            plugin_root = (marketplace_path.parent / source).resolve()
            plugin_json = plugin_root / "plugin.json"
            assert plugin_json.exists()

            plugin_data = _load_json(plugin_json)
            assert plugin_data.get("name") == plugin["name"]
