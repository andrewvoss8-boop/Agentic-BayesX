# Framing

## Engineering Decision

Decide whether the current agent workflow is structured enough to run a first multi-agent proof of concept without losing traceability or overstating results.

## Objective

Produce a complete first-loop packet with task, commands, checker output, sources, review notes, open risks, and next prompt.

## What Agents May Choose

Agents may choose which helper role is needed next and which existing checks to run first. They may not change the scientific objective or sampler standard during this first loop.

## What Remains Human Judgment

The human chooses whether the workflow is useful, whether the next loop should implement NUTS/HMC, and whether any durable notes or rules should be accepted.

## Wrong-Question Trigger

If the loop only proves that agents can write reports, but does not expose command outputs, checker status, reviewer concerns, and open risks, then the workflow is answering the wrong question.

