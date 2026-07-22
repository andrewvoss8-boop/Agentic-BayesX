#!/usr/bin/env python3
"""Static audit for the independent review and runner-card artifacts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent
REVIEW = ROOT / "review.md"
CARD = ROOT / "task_card_codex_structured_discrepancy.md"


def require(text: str, phrases: list[str], label: str) -> list[str]:
    return [f"{label}: missing {phrase!r}" for phrase in phrases if phrase not in text]


def main() -> int:
    errors: list[str] = []
    for path in (REVIEW, CARD):
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"missing or empty artifact: {path.name}")
    if errors:
        print("OVERALL RED")
        print("\n".join(errors))
        return 1

    review = REVIEW.read_text()
    card = CARD.read_text()
    errors += require(
        review,
        [
            "Overall review status: RED",
            "not done in this paper",
            "frequency- and location-dependent **covariance**",
            "logarithm of a dimensional accelerance",
            "eight arms",
        ],
        "review",
    )
    errors += require(
        card,
        [
            "AUTONOMOUSLY DISPATCH-READY — NO HUMAN APPROVAL PAUSE",
            "ln(|H1_meas(d,i,f_s)| / H_ref)",
            "c_d ~ Normal(c_bar, tau_c²)",
            "E[H_* beta | training]",
            "E[u_* | training]",
            "force `K_*T = 0`",
            "10 Hz guard",
            "S0 null",
            "no more than 1 of 20 seeds",
            "at least 16 of 20 seeds",
            "Automatic transition after Stage 1",
            "PROCEED_JOINT",
            "STOP_PARTIAL_MEAN",
            "J1 = E1 mechanism and J3 = E3",
            "max rank-normalized R-hat ≤1.05",
            "realized Stage 1 discrepancy floor",
        ],
        "card",
    )
    forbidden = [
        "a literature-wide genuine gap",
        "log of accelerance, g/lbf",
        "what Febrianto et al. do",
        "DO NOT START WITHOUT EXPLICIT APPROVAL",
        "DISPATCH-READY FOR HUMAN REVIEW",
        "Human checkpoint after Stage 1",
        "No joint NUTS run begins without explicit approval",
        "Run only if Stage 1 passes and approval is recorded",
    ]
    for phrase in forbidden:
        if phrase in card:
            errors.append(f"card: forbidden overclaim/contract text {phrase!r}")

    if errors:
        print("OVERALL RED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("OVERALL GREEN — static runner-card audit")
    print("Review and independent card exist; required conceptual, leakage, identifiability, and convergence controls are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
