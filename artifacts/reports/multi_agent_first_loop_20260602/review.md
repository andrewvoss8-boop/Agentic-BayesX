# Review

## Initial Review Status

The scaffold files exist and the scaffold checker passed. The existing fresh 2DOF workflow also replayed successfully. This is a workflow proof of concept, not a new scientific result.

## Known Open Risks

- Claude Code is not available on `PATH` in the current Codex shell, so the human may need to launch Claude through the Cursor extension.
- Cursor and Claude project-agent support depends on the installed extension versions.
- Existing inference artifacts still use prototype/legacy random-walk/random-scan Metropolis, not NUTS/HMC.
- The first loop verifies workflow coordination; it does not improve the structural model.

## Check Evidence

- Fresh 2DOF payload: pass.
- Fresh 2DOF checker: pass with 30 numerical assumptions and Ch2/Ch3 relative L2 = 0.6739064407171255.
- Scaffold checker: pass.
- Immutable checker hashes: pass.

## Reviewer Checklist

- Check that commands were actually run and exit codes were recorded.
- Check that no immutable checker file changed.
- Check that helper claims point to files or command output.
- Check that current sampler language does not imply NUTS/HMC is implemented.
- Check that the next prompt identifies one narrow next loop.
