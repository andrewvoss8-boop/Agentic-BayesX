# Priority Deliverables — notch_multipoint_7004c_20260611

Andrew's ask (2026-06-11 chat, verbatim intent): "prepare a series of thorough analytical
numerical examples to show the behavior and empirical ideas that shape the behavior when
compared with the tools in 7004c. Create figures and gifs to teach the evidence, and a
powerpoint to summarize it. I will leave it to your judgement as for what to use to
answer my curiosities."

| # | Priority ask (restated) | Interpretation chosen (delegated judgment) | Delivered at |
|---|---|---|---|
| P1 | Analytical numerical examples comparing multi-point/6-DOF behavior against the 7004C tools | Four examples: EX-A replicate 7004C's own TDOF impedance example (Fig 8/9, Eq 1-2, Eq B1-B2) as the verified baseline; EX-B rigid box on 4 spaced feet -> 6x6 apparent-mass matrix, bounce vs rocking, effective masses, per-foot vs net force ("resultant trap"); EX-C the same payload on a compliant plate backing -> where the notch is visible vs distance from a foot (the "how far" question); EX-D force-limited shaker test of the multi-point payload -> net-force limiting vs moment limiting vs flight truth | `code/ex_[a-d]_*.py`, `results/ex_[a-d]_results.json`, packet.md §3-§6 |
| P2 | Figures that teach the evidence | ~16 figures, each stating run/data provenance per AGENTS.md plot gate | `figures/*.png` |
| P3 | GIFs that teach the evidence | 3 GIFs: TDOF notch sweep (absorber intuition); rocking resultant-trap animation; plate notch-field frequency sweep + ODS | `figures/*.gif` |
| P4 | PowerPoint summary | `7004c_multipoint_notch_summary.pptx`, ~15 slides, beginner-ML/advanced-structures audience per CLAUDE.md | workspace root |
| P5 | Answer the three curiosities | Direct answers in packet.md §7 and final PPT slides, each tied to a numbered figure/number | packet.md, pptx |

Ambiguity handling: Andrew explicitly delegated scope/model choices; interpretations
above are recorded as decisions D2-D5 in `decisions_log.md` rather than re-asked.
Acceptance: every behavior claim has a checker-verified number or labeled figure;
check.py green/yellow/red per AGENTS.md Result Status Standard; `bash run_all.sh`
replays end-to-end.
