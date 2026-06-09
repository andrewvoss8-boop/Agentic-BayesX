# Modeling-Freedom / Anti-Overfitting Experiment

**Question being answered (methodology, not science):** can a single Opus runner be given broad
freedom to try many model architectures / discrepancy structures / priors / hyperparameters and
run ablations, and still pick a winner WITHOUT overfitting — and do the anti-overfitting
guardrails catch overfitting when it happens?

Read [contract.md](contract.md) (frozen evaluation contract) and [splits.json](splits.json) first.

## Layout
- `contract.md`, `splits.json` — FROZEN once the vault is on Google Drive (hashes in `manifest.sha256`).
- `scripts/gen_synthetic_tray.py` — generated the synthetic controlled substrate.
- `scripts/build_shocksat_split.py` — declared the real ShockSat train/dev + held-out pyro regime.
- `scripts/score_vault.py` — HUMAN-ONLY grading (run by Andrew after finalists are locked).
- `runner_opus/inputs/{train,dev}` — synthetic observations the runner may use (NO truth).
- `runner_opus/inputs/shocksat/inputs_manifest.json` — read-only real inputs (paths + SHA256).
- `vault/tray/` — SEALED synthetic truth → uploaded to Google Drive + deleted locally. **Never commit plaintext.**
- `vault/shocksat/held_out_manifest.json` — held-out pyro regime (audit-enforced + hash-pinned).
- `manifest.sha256` — pinned hashes (contract, splits, vault archive, held-out + real inputs).

## Vault mechanism (both substrates airtight)
- **Synthetic** = airtight: truth exists only in `vault/tray` → Google Drive + local delete.
  Integrity = SHA256 of the vault archive committed BEFORE upload; verified on re-download at grading.
- **ShockSat** = airtight (physical): the pyro regime is staged, uploaded to Google Drive, then
  deleted from local disk (including the parked sibling run) until grading; SHA256 pinned and
  verified on re-download; checker also greps for the path (defense-in-depth). Restorable after
  the experiment (re-fetch from NASA / re-download). Possible only because the ShockSat-science
  line is PARKED, so the file is not needed on disk meanwhile.

## Status
Generated + sealed locally 2026-06-09, **pending Andrew's Google Drive upload + local delete of
`vault/tray/`**. Until that upload, every frozen choice remains reviewable. The runner has not run.
