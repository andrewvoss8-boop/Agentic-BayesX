# Decisions Log

## D1: Tool-specific element choices

Human instruction: "work the specific element options available in each tool faithfully to best FEM practice in that tool and the actual structure."

Decision:

- Use solid/shell tray elements rather than a pure 6-DOF rigid tray where practical, because Phase 1 must expose tray-flex modes.
- Use axial truss/rod struts for the solved Python paths and decks because spherical rod ends make the struts two-force members. This is faithful for suspension modes but does not capture strut bending self-modes.
- Keep explicit apex joint nodes in every build so later compliance can replace the rigid tie without moving the interface definition.
- Use stiff translational joint ties or rigid multipoint ties for Phase 1 only. All rigid-joint frequencies are provisional upper bounds.

## D2: CalculiX availability

`ccx`/`ccx_2.21` was not available on PATH, and Homebrew was not available. The CalculiX cell therefore generated the input deck and geometry figure but did not claim solved frequencies.

## D3: No pre-loaded target

No frequency target was used or tuned against. Reported Python frequencies come directly from each build's assembled eigenproblem.
