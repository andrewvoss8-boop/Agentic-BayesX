# Priority deliverables — ShockSat advisor closure brief, fable revision

Question this task answers: apply Andrew's docx review (comments C0–C9 and his rewritten closing) to a
copy of the advisor brief, in a new `_fable` workspace, without changing any scientific claim or number.
Every number must still resolve to the frozen Task Card A / study artifacts; no new inference or scoring.

Priority order:
1. `ShockSat_Bayesian_FEM_StatFEM_closure_brief_fable.docx` + `.md` — revised brief implementing all ten
   review items, with the two "why the mean cannot move / why the bands stay wide" statements made
   explicit (CENTRAL FINDING callout, §2 subsection, §5 WHY WIDE), Andrew's closing kept verbatim.
2. `figures/fig2_modular_frf_panels.png` — six held-out FRF channels selected by the preregistered
   miss-rank rule (decisions_log.md F2), from stored arrays only.
3. `out/numeric_trace.json` + `out/source_manifest.json` — unchanged trace discipline (31 spot checks).
4. `check.py` (adapted per decisions_log.md F4) passing with no RED; render + QA outputs in `qa/`.
5. `packet.md` — plain-English summary with checker output verbatim.

Out of scope: any new likelihood, sampler run, metric, or claim; edits to the v1 workspace; durable-note
changes beyond the standard `notes/runs.md` entry and the lead CURRENT STATE block.
