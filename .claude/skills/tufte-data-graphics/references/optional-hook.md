# Optional: wire the linter as a Claude Code hook (needs your approval)

The skill above is **model-invoked**: Claude reads it whenever a task matches the
`description` (generating/editing a graph of numeric data). That covers "called
when we generate graphs" without changing any durable config.

If you also want a **deterministic** nudge that fires every time a plotting file
is written, add a `PostToolUse` hook. This edits `.claude/settings.json`, which is
durable harness config — per the project rules I will not enable it without your
explicit approval. Paste this yourself, or approve and I will.

```json
{
  "agent": "lead",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "f=\"$CLAUDE_FILE_PATH\"; case \"$f\" in *.py) if grep -lqE 'matplotlib|pyplot|seaborn|plotly' \"$f\" 2>/dev/null; then echo '[tufte] plotting file touched — run: python3 .claude/skills/tufte-data-graphics/scripts/tufte_lint.py '\"$f\"' and apply the SKILL.md checklist'; python3 .claude/skills/tufte-data-graphics/scripts/tufte_lint.py \"$f\"; fi;; esac"
          }
        ]
      }
    ]
  }
}
```

Notes:
- The hook only prints advice; it never blocks. The linter is heuristic — review
  each flag against intent.
- `$CLAUDE_FILE_PATH` is the file Write/Edit just touched; the `case`/`grep` guard
  keeps it quiet for non-plotting files.
- Verify the env-var name and hook schema against your installed Claude Code
  version before relying on it (hook APIs change; this is marked TO-VERIFY).
- This hook mechanism is Claude-Code-specific and does not transfer to
  Codex/Cursor; for those, the skill is mirrored as guidance, not a hook.
```
