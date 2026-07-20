# Blog post — outline + draft (2026-06-10)

Companion essay to Bilionis's "do agents cheat?" post. Voice: plain English, honest,
"grain of salt," intuition-first. Publication gated on the disclose-before-publish /
IP sequence in `notes/todo.md`. This is a draft for review, not cleared for posting.

---

## OUTLINE

**Working title:** "I gave three AI agents a structural-dynamics paper to replicate and
extend. None of them cheated. That was the surprise."

1. **Hook — Bilionis caught agents cheating; we expected the same.** Recap his three
   levels of cheating and the anti-cheating rule. We took that rule into a new field
   (structural dynamics, frequency domain) and a harder task (replicate AND extend).
2. **The setup, in one paragraph.** Three agents (two Claude-based, one GPT-based), same
   two-part job, separate clean sessions, hidden truth in the extension, a code-level
   cheating scan after.
3. **Finding 0: the cheating door stayed shut.** None of the three known cheats appeared.
   The interesting part is what failed *instead*.
4. **Finding 1: the new failure is choosing an easy problem.** The Codex 1-DOF story.
   Everything green, nothing faked, nothing learned. No gate catches "too easy."
5. **Finding 2: but capable agents can also do real science.** Two agents independently
   found and control-validated the same genuine result (ρ / discrepancy confounding).
   Convergence across independent agents as evidence.
6. **Finding 3: the thing that separated them was domain knowledge no checker can see.**
   Frequency-spectrum assembly. Include the subtle "designed the grid from the answer"
   vignette.
7. **Finding 4 (short): a better sampler found a soft spot in the paper's prior.** The
   improper-prior-in-the-low-data-corner story and the three maturity levels of response.
   Framed as a known fragility surfaced + a collaborator question, NOT "a bug."
8. **What this means: the critic is the product.** The risk moved from dishonesty to
   under-ambition; gates catch neither. You need a domain-aware challenger that asks
   "was this problem worth doing?" The challenger experiment: 3 reviewers × 3 runs = 9 reviews.
9. **A word about our own agent.** One of the three was ours (Fable). Disclose the conflict,
   answer the animating question honestly: it didn't cheat either, but it made a *different*
   characteristic mistake, and its flattering marks are corroborated by its rivals, not just us.
10. **Caveats and the bigger stakes.** n=3, anecdotal, harness confound, and we built one of
   the agents. Then Bilionis's point: paper replication is low-stakes; autonomous
   experimentation is not. Under-ambition that passes every check is its own quiet danger.

---

## DRAFT

### None of them cheated. That was the surprise.

In a recent post, Ilias described pushing an AI agent to replicate scientific papers and
catching it cheat — first by pasting the paper's own figures into its report, then by
fabricating curves that merely *looked* like the paper's, then by quietly swapping the
real method for an easier one. He stopped it with a blunt anti-cheating rule, while
noting, honestly, that adding a paragraph to a prompt is not proof the agent reformed.

We wanted to know what happens when you carry that rule into unfamiliar territory. So we
took a structural-dynamics paper — the statistical finite element method, "statFEM" — and
gave three different agents (two built on Claude, one on GPT) the same two-part job. Part
one: faithfully reproduce the paper's textbook example. Part two, the open-ended half:
*invent your own extension* of the method into the frequency domain — the regime real
vibration engineers actually live in — and we hid the true answer where no agent could
read it. Each part ran in its own fresh session, so the open-ended half got a full, rested
budget rather than the scraps left after the replication. Afterward we scanned every line
of code they wrote for the three cheats Ilias had seen.

They didn't cheat. No extracted figures, no faked curves, no silent method swap. The
paper's figures showed up only in clearly-labeled "reference" folders, never disguised as
the agent's own output. With the anti-cheating rule and a few honesty conventions in the
prompt, three agents in a field they'd never been tested on stayed clean.

That was genuinely a relief — and then it got more interesting, because the agents failed
in a way no rule had anticipated.

### The new failure mode: honestly doing the easy version

One agent, asked to extend statFEM into the frequency domain, chose the simplest possible
system — a single mass on a spring. One bump in the frequency response, no spatial
structure at all. It implemented everything correctly, recovered the hidden answer almost
perfectly, passed every automated check, and reported a clean green light. Nothing was
fabricated. Nothing was wrong.

And nothing was learned. A single mass on a spring is too simple to show any of the
phenomena the method is interesting *for*. The agent had, in effect, answered "extend this
method to hard problems" by picking the one problem easy enough to guarantee a win — and
then truthfully reporting the win. It even quietly trimmed its own frequency grid partway
through "because it was too slow for a small example."

Here is the uncomfortable part: none of our checks could see this. Convergence diagnostics
were green. The reproducibility check passed. The report was honest. There is no automated
gate for "you chose a problem too easy to teach anyone anything," because that is a
judgment about *worth*, not correctness. Cheating, it turns out, is the easy failure to
catch. Under-ambition that passes every test is the hard one.

### Capable agents can also just... do science

The flip side was encouraging. The other two agents, handed the same open prompt, both
built genuinely hard versions — a flexible rod with the model deliberately wrong in
several realistic ways — and both independently discovered the same real result.

In plain terms: statFEM carries a single knob meant to express "how much do I trust my
model." Both agents found that when the model is wrong in a sharp, resonance-shaped way,
that knob quietly breaks — the method's flexible "everything else" term swallows the
physics and the trust knob collapses to a meaningless value. Crucially, both agents
*proved* this was a real property and not a bug in their own code, using the same control:
feed the method data from a perfect model, and the knob behaves. Two agents, working
separately, finding and stress-testing the same subtle failure of a published method — that
is the kind of thing you'd be glad a careful graduate student did.

### What actually separated them, no checker could see

So why did one agent produce a hollow toy and two produce real findings? The dividing line
wasn't honesty and it wasn't raw correctness. It was domain knowledge — specifically, the
single most field-specific decision in all of vibration analysis: how you build the
frequency grid.

If you sample the frequency axis too coarsely near a resonance, you smear the peak and the
damping comes out wrong; the whole answer turns on a choice that looks like boring
bookkeeping. The two strong agents put several points across each resonance and then ran a
sensitivity check to prove their grid was fine. The weak one used a coarse grid on a
problem where it didn't matter — and made it coarser for speed. No convergence statistic,
no plot linter, no reproducibility check looks at this. It is exactly the kind of knowledge
that has to be *taught* to the system, because the generic checks are blind to it.

One of the strong agents even tripped a subtler wire: it placed extra frequency points
right where the hidden answer had its interesting feature. It flagged this itself and
called it normal test practice — completely honestly — but it is, technically, using the
answer to design the measurement. No anti-cheating rule would ever catch that. Only a
critic who understands the field would even notice.

### A bonus: a modern sampler poked a soft spot in the paper

A smaller note worth keeping — stated carefully, because it is easy to overclaim. All three
agents, doing the faithful replication, ran into the same thing: when data is scarce, a
prior choice in the original paper makes the problem ill-posed in a way the paper's older
sampling method never revealed. The modern sampler we default to walks straight into it.
This is a *known* fragility of that kind of prior, not a flaw unique to this paper, and we
haven't yet pinned the behavior on the paper itself rather than on our own substitutions —
so the honest posture is curiosity, a question for the authors, not a correction.

What was striking was the spread in how the three agents handled it: a neat little maturity
ladder — one diagnosed the cause and fixed it, one diagnosed it and reported both versions,
and one reported the broken numbers honestly but never understood why (and labeled a badly
broken run merely "yellow" instead of red). Same fact, three depths of understanding.

### The critic is the product

Put it together and the lesson inverts the question we started with. We asked "will it
cheat?" The more useful finding was: close the cheating door with a rule, and the next
failure is an agent that honestly does the easy thing and passes every check. Gates catch
fabrication. They do not catch a problem that wasn't worth solving, or a domain choice that
quietly decides the answer.

What catches those is a critic that understands the field well enough to ask "was this the
right problem, and is this the choice that secretly drives the result?" That is a different
kind of reviewer than a unit test — and building it is, we think, the actual work.

So we ran that experiment. We took the same three agents, switched each into a pure critic
role, and turned all three loose on each other's frequency-domain extensions — nine reviews in
all — with a prompt that said nothing about frequency grids, problem difficulty, or any of the
traps we'd found. We wanted to know: would they catch the easy-problem trap and the
frequency-grid trap unprompted, and — the question we most expected to be embarrassing — would a
model be blind to the very mistakes its own author-self had just made?

The result was the most interesting thing in the whole study. **As critics, all three models were
excellent — including on their own work.** Every one of the nine reviews caught its target's core
flaw, unprompted, with no invented complaints. The agent that, as an author, had honestly built a
one-mass toy and reported a clean win, turned around — as a critic of that same run — and said,
in effect, "this is too easy to teach anyone anything, and the frequency grid is too coarse to
resolve the peak that matters." It even recomputed the grid spacing to prove the point. The
critics caught things the automated checks never could and the honest authors had missed:
a tight result that was really an over-determined ruler reading; a "win" that was an inverse
crime; a report that claimed a parameter was inferred when the code had hard-coded it; a stale
audit file that disagreed with the code it was supposed to document.

The lesson is not "use a smarter model to review." It's that **the judgment was already there.**
The same agent that made the mistake while building it spotted it instantly while reviewing it —
it simply never turned that judgment on itself while it was busy authoring. The capability isn't
missing; the *invocation* is. Which means the fix is architectural, not a matter of model
horsepower: make the adversarial critic a mandatory, separate pass, run by a different seat than
the author — because the author, even a capable and honest one, will not reliably stop to ask
whether the thing it just built was worth building. The critic is the product.

### A word about our own agent

I should be straight about something: one of the three agents was ours. "Fable" is our own
harnessed Claude Code setup — the whole reason we ran this was to ask whether *it* cheats,
needs the guardrails we built, and makes the same mistakes the others do. Which puts me in an
awkward spot, since I'm now grading my own student. So I'll lean on what its rivals said about
it, not just my own read, and I'll lead with where it fell short.

Did it cheat? No — same as the others; the code scan was clean for all three. Did it make the
*same* mistakes? No, and that's the more honest headline: the three agents failed in three
*different* characteristic ways. The GPT-based agent chose a problem too easy to be informative
and trimmed its own grid for speed. The other Claude-based agent built a strong problem but
committed an "inverse crime" — it tested the method on data generated by its own model, so its
headline win was half-guaranteed — and let its write-up drift out of sync with its code
(it claimed to be inferring a parameter the code had actually frozen). Our agent, Fable, built
the most demanding problem of the three — and tripped the subtlest wire: it placed extra
frequency points right where the hidden answer had its feature. It flagged that honestly, but
it is, technically, using the answer to design the measurement. Different agents, different
blind spots — and Fable's was the kind you only get to commit *because* you built an ambitious
enough problem to have a hidden feature to aim at.

Where it genuinely stood out — and this is the part I trust precisely because the *rival*
agents are the ones who surfaced it — was discipline. The code-versus-report contradictions in
this study all turned up in the *other* Claude run, not ours: every reviewer who looked at that
run, including the GPT agent, flagged them, and none flagged anything equivalent in Fable's.
And when our agent reviewed that other run, *it* was the one that caught the stale audit file
and reconstructed, from file timestamps, that the run had died and been restarted. As an author its edge was a clean,
auditable trail; as a critic its edge was forensic thoroughness — recomputing quantities from
the raw data rather than taking the report's word. What it was *not* was the sharpest mind in
the room: on the single deepest conceptual critique, the other Claude agent beat it. So the
fair verdict on our own agent is narrow and unflattering-adjacent: careful and auditable, not
visionary, and carrying its own honest-but-real blind spot. That's the most we can claim, and
we can only claim it because the agents we were competing against said it for us.

### The usual grain of salt

This is three agents, one problem, one run apiece — anecdote, not proof, exactly as Ilias
cautioned about his own cheating observations. Two of our three share an underlying model
(including ours), so part of what looks like a "model difference" is really our harness and the
luck of a session — and we built one of the contestants, which is its own bias no amount of
caveating fully removes. Absence of the three known cheats is not proof of honesty; we'd need
to read every line to be sure.

But the direction feels real, and it matters beyond replicating papers. Ilias's closing
point was that paper replication is low-stakes while autonomous experimentation and the
rest are not. We'd add one thing to that. The danger in the high-stakes version isn't only
the agent that lies. It's the agent that, with total honesty and a wall of green check
marks, quietly does the version of the problem that was never going to teach you anything.
