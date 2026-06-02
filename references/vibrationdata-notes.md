# vibrationdata Notes (Trace)

Purpose: map implemented checks to classical 2DOF/MDOF vibration sanity checks.

## Planned tie-ins
- Verify resonant behavior near assumed natural frequencies.
- Verify apparent-mass and transfer-function shape trends.
- Verify coupled vs standalone tray behavior changes.

## Check mapping
- `tests/test_posterior_recovery.py`: posterior recovers synthetic truth in simple settings.
- `tests/test_mdof_transfer.py`: reduced-order transfer function shape and dimensions.
