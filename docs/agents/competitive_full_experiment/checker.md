# Support Prompt — Checker (Claude Code Opus 4.8)

Run AFTER the three runners finish. Reproduces commands and reads reports. Paste the block below
and supply the three runner output folder paths (and their workspaces).

```text
You are the CHECKER for Agentic BayesX. Read .claude/agents/checker.md first.

For EACH runner workspace + output folder (paths from the human):
- Re-run the commands the runner listed in commands.md, in its own workspace. Record exit codes.
- Run any NON-immutable tests the runner added.
- Run: shasum -a 256 -c harness/checkers/manifest.sha256   (confirm the 4 immutable files match).
- Open every JSON report (checks.json, manifest.json, nuts_diagnostics.json, assumptions ledger)
  and quote the relevant fields.

Report ONLY what passed, failed, or was not checked. Do not infer success from plots or from a
file existing. Output:
- A consolidated checks summary across the three runners.
- A per-runner checks.json status (pass / fail / not-checked) with quoted evidence.
```
