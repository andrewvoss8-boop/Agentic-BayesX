# Priority deliverables (human direction 2026-11-16)

| Ask | Interpretation | Delivered | Status |
|---|---|---|---|
| Save the recovered extract (zip + download) | zip the 29 MB text extract, send it, keep a durable copy | zip sent in chat 2026-11-16 (SHA-256 e2840c3f...753970b); committed to private repo branch `claude/ecstatic-carson-c3e4f9`, folder `recovered_text_extract/` (3,564 files with manifest) | done |
| Headers-only request to FEM_and_CAD.zip | `curl -I` and a Python probe | refused by this cloud environment's network policy (proxy 403), 2026-11-16 21:17 Z, 2026-11-17 02:04 Z, 11:31 Z, 11:47 Z; `logs/gate_status.json` | blocked |
| Pull only `Correlation/` by byte range and parse the burst files | exact member list and byte ranges from the archive's own table of contents; tested ranged fetcher; binary probe; one command | `out/fetch_plan.json`, `code/zipfetch.py`, `code/adf_probe.py`, `gated_run.sh` | staged, waiting on network |
| Continue the research autonomously, results on GitHub, no local disk | work in the cloud container, push both branches | this workspace; notes updated | done to the network bottleneck |

Assumed interpretations (flagged): "the plan" is reconstructed from the human's messages (not in either repository); "about 1 GB" for `Correlation/` is corrected to 1.96 GB compressed for the whole folder, 0.73 GB for what the plan needs.
