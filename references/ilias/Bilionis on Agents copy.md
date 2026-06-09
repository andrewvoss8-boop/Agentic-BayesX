

clarification from dr. bilionis:
ME:
I'm leaning towards making bayesian updating (a la Girolami/StatFEM) the main focus of the project since it builds off my industry expertise and is within the labs expertise.  To include a good experimental component, I'll need to spend $100-500 or let the Vandy Lab I used to work in during undergrad (LASIR) let me do some testing there.  It can also be accomplished with just synthetic examples, but that's a bit boring.   Relativity is not as interested in this project except for the piece on the damping parameter at non-linear interfaces.

They are more interested in design optimization algorithms which are less in my experience and the PSL specialty, but I did meet with this author and he is willing to get me setup with an NDA and his code/workflows.  He is proposing to me an element of his research that really badly needs "AI" but think what he means is not something I have experience with. ( There is a piece where I think he could really use bayesian optimization too, but he hasn't bitten on that really).  Relativity would be interested in that project to the extent that it actually achieves the goal of lightweighting their trays and helping with vibe.  I think working on this makes more sense as a side project that is not the main thing.  I just am not confident I could make a meaningful contribution in 2 months with the skills I have in that area.  I'd mostly be a learner and fully dependent on how much help Todd (the author) could provide by way of assistance.

So I essentially need to know from you what is most strategically valuable for you and the lab.  Would you be excited to branch out into Hyperstructure optimization and establish the connection with Todd and also spend the 2 months trying to maximize value for relativity because that could be a formal research partnership in the future (I think they established their first formal lab relationship with Zucrow this spring?  Or does it make more sense to focus on the project that builds off my career experience and our lab's experience and nurture the relationships with relativity and Todd casually?  And if I do pursue an experimental component, how much $$ can I count you in for?
Him:
The most useful thing for me right now would to work on something that builds upon coding agents like Codex and Claude code. For example, develop skills and harness that enables them to solve correctly a class of engineering problems.
Of even greater importance, would be to have an agent control experimental equipment to run fully autonomous experiments
This is the future
There is no problem covering $500 experimental costs.



	His Substack post:


Why Scientific Autonomy Needs a Harness
I repurposed Karpathy's autoresearch idea for scientific machine learning
Democratizing Science with AI
Mar 23, 2026

It’s been a while since I last posted. But this post took me about 16 hours to put together. And I’m not counting the more than 80 hours I spent during spring break experimenting with agentic patterns… You can find my git repo to replicate this work here.

Thanks for reading! Subscribe for free to receive new posts and support my work.

Coding agents like Codex and Claude Code can already accelerate research and development.

However, the default way of using them requires a human supervisor to constantly review and nudge the agent to keep it on the right track. We have run many paper replication experiments, as well as more targeted scientific machine learning studies (e.g., building a computationally inexpensive surrogate for an expensive PDE solver). A recurring problem is that, over time, the agent's context drifts. What was in the prompt at the beginning of the run tends to be forgotten; the agent stops, asks a stupid question, declares victory after a small improvement, or just takes shortcuts.

The idea of a harness
A harness is an infrastructure around the agentic loop that can endow an agent with long-term memory and keep it on track. OpenClaw’s harness is exactly one of the reasons behind its success. There are two ways you can build a harness: prompt injection and code scaffolding.

Harness from prompt injection
The first time I heard about a harness based on prompt injection was Ryan Lopopolo’s post Harness engineering: leveraging Codex in an agent-first world.

The idea is straightforward: you create a Markdown file with instructions the agent must follow no matter what, and you inject it into the prompt at every step of the loop.

With Codex, this can be done by using the AGENTS.md file (Claude Code uses CLAUDE.md). The file AGENTS.md is a simple text file that you put in a work directory. Once Codex enters that directory, it automatically reads the file. Then it keeps it in its context. If the context is compacted, it may read it again. The idea is that Codex tries to satisfy what is in both the prompt and the AGENTS.md (if possible).

So, what do I put in this file? For our workflows, I typically give them some basic rules to follow that aim to enforce the scientific method, set up a simple memory system, and guide when they can consider a task done.

It looks like this:

# AGENTS.md

Build for correctness, reproducibility, traceability, and continuity.

## Rules:
- Don’t guess silently. Mark assumptions explicitly.
- Inspect relevant files before changing code.
- For nontrivial work, make a short plan first.
- Prefer small, focused changes over broad refactors.
- Write artifact-backed outputs, not just prose.
- Validate before claiming success.
- If blocked, say exactly why.

## Memory:
- Do not rely on conversational memory across sessions.
- Write important decisions, lessons, pitfalls, and next steps to repo-local notes.
- Prefer short dated notes in `notes/memory.md`, `notes/runs.md`, and `notes/todo.md`.

## A task is done only when:
- the requested artifact/code exists,
- the main checks were run,
- assumptions and limitations are stated,
- and outputs are easy to trace and replay.

When I use Codex to build a big system, with lots of files, and so much code that it doesn’t fit in the context, I try to do two things. First, I explain how it can organize memory hierarchically so it can find things quickly.

I may write something like this:

## Memory:
- Do not rely on conversational memory across sessions.
- Write important decisions, lessons, pitfalls, and next steps to repo-local notes.
- Prefer short dated notes in `notes/memory.md`, and `notes/todo.md`.
- Use a hierarchical structure to organize the notes. For example, you can have a 
  `notes/` directory with subdirectories for different topics, and within each
  subdirectory, you can have dated markdown files that capture the relevant information.

Second, I may enforce some basic systems engineering principles, e.g.,

## Rules:
- Use `design/` for high-level design documents and architecture decisions.
  Organize design hierarchically in system, subsystem, etc. Each system has 
  requirements, conceptual design which decomposes into subsystems. 
- Use `src/` for implementation code.
- Use `tests/` for test cases and validation scripts.
- A subsystem is complete when it has a design document, an implementation, 
  and a test that validates the implementation against the design.
- A system is complete when all its subsystems are complete and it has an 
  integration test that validates the system against the requirements.
- Always rerun the relevant tests after making changes to ensure that the
  system remains correct and that you have not introduced regressions.

That said, I’m not entirely sure that this is indeed the best way to design a complex system, but that’s another discussion.

Harness from a scaffold: Karpathy’s autoresearch idea
Andrej Karpathy recently published the autoresearch git repo. The idea is to build a harness for the agent to streamline neural network hyperparameter tuning.1 The harness essentially gives the agent's workflow a structure. You give the agent a way to prepare a solid baseline and objective validation metrics. You also give it a specific way to implement its changes.

Let’s look into the basic ingredients and the mechanics that it enforces:

The problem, data, validation metrics, and whatever stays unchanged go in a file named prepare.py. The agent is not allowed to touch this file.

The current model and training algorithm go in the file train.py. This is the file that the agent edits on its iteration.

The file program.md is the prompt that establishes the harness. Karpathy’s version is here. I am not going to copy-paste it, but it is instructive to read it. The harness establishes the following:

Use git to keep track of every trial.

Each trial is: Modify train.py. Run the evaluation, track results. If improved, keep the change. If not improved, discard it.

Applying Karpathy’s harness to PDE operator learning
I wanted to see how Karpathy’s idea works in practice for scientific machine learning problems. You can find my work in this git repository. I first tried a standard physics-informed neural network (PINNs) problem.2 But Codex was so good at coding the PINN baseline that it was hard to get any improvement.

So I switch to a harder problem. The task is to learn a surrogate operator of the Burgers’ equation. The inputs are:

the viscosity

an initial condition (a function of space).

The outputs are:

the full spatio-temporal Burgers solution field.

We have to learn this operator from a finite number of input-output pairs.

Stochastic model of the input
The initial condition is not sampled from one fixed template. It comes from a hierarchical Gaussian random field prior. I first sample kernel hyperparameters from a prior, and then sample the initial condition from a Gaussian process conditioned on those hyperparameters. Codex coded up the sampling of this hierarchical Bayesian model in one shot.

The data
To generate training, validation, and test data, I asked Codex to make a numerical solver for Burger’s equation. It also did it in one shot.

I asked it to generate:

100k training examples

20k validation examples

500 test examples

Generating the data took about 3 hours.

The training data are used, well…, for training. The validation data are used to objectively measure improvement after each autoresearch loop. The test data are saved for the final tests.

How I developed the harness for this problem
I repurposed Karpathy’s autoresearch by just editing prepare.py, train.py, and program.md to fit the Burgers surrogate problem and ensure things run on the cluster GPUs. I should note that I made these modifications entirely in Codex. I did not actually have to write any code myself. I just described the problem to Codex, iterated with it for about 2-3 hours, and it got it right.

How to run the experiment
I ran the experiment through a Codex session with the --dangerously-bypass-approvals-and-sandbox flag so that I don’t have to constantly approve what it’s doing. Be careful with this.

I have installed in my ~/.codex/skills the following skills from our lab repo.

cluster-slurm: teaches Codex how to access the GPU cluster

jax-fast-code: teaches Codex how to write good JAX code.

Being in the autoresearch directory, I just ask my Codex to launch a subagent to run the autoresearch loop 20 times.

The 20 iterations took about 7 hours on an H100 GPU.

Results
It worked remarkably well. Here is the performance evolution:





The initial architecture (that Codex came up with) was:

Initial architecture

DeepONet

a resmlp branch with width 256 and depth 4

a plain MLP trunk with width 256 and depth 4

SiLU activations throughout

Fourier coordinate encoding with 64 random Fourier features and scale 3.0

latent rank 192

The best architecture it found was the same, but with increased capacity:

DeepONet

The branch stayed resmlp, but the width increased to 640

The trunk stayed a plain mlp, but the width increased to

640

The depth stayed 4 on both sides
activation stayed SiLU

Fourier encoding increased from 64 to 96 features
latent rank increased from 192 to 448

And here are some test predictions on specific time slices:




And complete spatio-temporal predictions:




The most remarkable thing is that Codex already provides a pretty good baseline. It seems to understand DeepONets pretty well!

Lessons learned
The harness is essential for autonomous computational work with Codex/Claude Code. There is no question about it. Without a harness, you have to hold the agents hand all the way through. Karpathy’s autoresearch does work when you have a narrow scientific task that has a very objective way to be validated. Hyper-parameter optimization (as we do here) is such a task. Most computational tasks do not quite fit this paradigm, but the paradigm could be extended to cover them.

Limitations
Despite the clear evidence that current agents can accelerate computational work significantly, humans still need to be in the loop to setup the right problems and to keep the agents from drifting.

Big computational workflows require stiching together multiple small tasks that may be amenable to an autoresearch approach, but we don’t quite know how to do this effectively yet.

Where this is going
I believe that current agents are very capable. Maybe as capable as we need them to be. I’m not sure how much we can still improve them.

I believe that we need more work on how to effectively use these agents. We need ideas for harnesses/scafolds that fit specific problem classes. Karpathy’s autoresearch is one such idea.

I believe that we are going to soon discover more innovative usage patterns, especially on the meta-level, e.g., or patterns that adjust autoresearch to a new problem, patterns that decompose a big problem into little autoresearch chunks, etc.


https://ebilionis.substack.com/p/why-scientific-autonomy-needs-a-harness


https://github.com/PredictiveScienceLab/autoresearch-pinns/tree/autoresearch/mar22b