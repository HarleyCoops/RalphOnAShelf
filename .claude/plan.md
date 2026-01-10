# Plan: Fix /ros Plugin Discovery

## Root Cause Analysis

The `/ros` command isn't being discovered because of **two issues**:

### Issue 1: Wrong plugin.json location
Claude Code looks for the plugin manifest at `.claude-plugin/plugin.json` (inside a `.claude-plugin` subfolder), but that file is **missing the command/hook/agent paths**.

**Current `.claude/plugins/ralph-on-shelf/.claude-plugin/plugin.json`:**
```json
{
  "name": "ralph-on-shelf",
  "description": "...",
  "author": {...}
}
```

**Should be:**
```json
{
  "name": "ralph-on-shelf",
  "version": "0.1.0",
  "description": "...",
  "author": {...},
  "commands": "../commands/",
  "hooks": "../hooks/",
  "agents": "../agents/"
}
```

The root-level `plugin.json` has the paths but Claude Code doesn't read that file.

### Issue 2: Duplicate plugin directories
There are two plugin locations causing confusion:
- `.claude-plugins/ralph-on-shelf/` - Non-standard, not discovered
- `.claude/plugins/ralph-on-shelf/` - Official location, but manifest is incomplete

## Fix Plan

### Step 1: Update the official plugin manifest
Update `.claude/plugins/ralph-on-shelf/.claude-plugin/plugin.json` to include:
- commands path: `"../commands/"`
- hooks path: `"../hooks/"`
- agents path: `"../agents/"`
- version: `"0.1.0"`

### Step 2: Verify the command files exist
Ensure these files are present in `.claude/plugins/ralph-on-shelf/`:
- `commands/ros.md`
- `commands/ros-mcp.md`
- `commands/cancel-ros.md`

### Step 3: Test the plugin
Restart Claude Code and verify `/ros` appears in available skills.

### Step 4: Clean up (optional)
Consider removing the duplicate `.claude-plugins/` directory to avoid confusion, or keep it as a development copy and use `--plugin-dir` for testing.

## Expected Outcome
After fixing the manifest, these commands should be available:
- `/ros` - Start a Ralph-On-Shelf autonomous loop in an E2B sandbox
- `/ros-mcp` - List available MCP servers
- `/cancel-ros` - Cancel active loop
