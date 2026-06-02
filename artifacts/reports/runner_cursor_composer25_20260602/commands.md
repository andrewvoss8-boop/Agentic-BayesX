# Commands

## Environment
- System Python: 3.9.6
- Created `.venv` with pinned `requirements-runner.txt`
- `pip install jax==0.4.23 jaxlib==0.4.23 numpyro==0.13.2 scipy==1.11.4 arviz pillow`
- NumPyro 0.20 + latest JAX failed on py3.9 (`match` syntax); pinned older stack.

## Replay
```bash
bash scripts/run_sequential_vibe_modal_flight_inference.sh
```
- inference exit code: 0
