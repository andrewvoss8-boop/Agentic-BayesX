# Priority Deliverables — notch_lit_review_20260612

Andrew's ask (2026-06-12): run the self-contained literature-review prompt from the
7004C multi-point study, using web/library access, and write the outputs under this
workspace.

| # | Priority ask | Interpretation / acceptance criterion | Delivered at |
|---|---|---|---|
| P1 | Literature review organized by questions A-H | Each section distinguishes source tier and cites verified sources with author/year/venue/DOI or URL. In-house claims 1-4 are marked CONFIRMED / PARTIALLY-KNOWN / NOVEL-AS-FAR-AS-FOUND / CONTRADICTED. | `lit_review.md` |
| P2 | Deduplicated bibliography | Full references for all cited sources; unverified or inaccessible sources marked clearly. | `bibliography.md` |
| P3 | Novelty and FTO notes | Candidate novelty vs prior-art table; patent summaries including US8731868B2; crowded/open assessment; explicit not-legal-advice and disclose-before-publish caveats. | `novelty_and_fto_notes.md` |
| P4 | Gaps and next experiments | Literature gaps mapped to ShockSat x tray / coupled-model follow-on tests. | `gaps_and_next_experiments.md` |
| P5 | Coverage / decisions log | Search scope, databases, dates, and inaccessible sources recorded for continuity. | `decisions_log.md` |
| P6 | Artifact-backed validation | Checker verifies required files, A-H sections, in-house status labels, source-tier tags, patent caveats, and no RED unverified-citation placeholders. | `check_review.py`, `checker_report.json` |

Ambiguities / assumptions: source access is limited to open web, patent databases,
NASA/ESA/standards landing pages, publisher abstract pages, and accessible PDFs.
Paywalled full texts are not treated as read unless accessible in this session.
