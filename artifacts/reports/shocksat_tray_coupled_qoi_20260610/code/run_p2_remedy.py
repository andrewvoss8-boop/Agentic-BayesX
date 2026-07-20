#!/usr/bin/env python3
"""p2 remedy run (D16): 4x(2000+2000) depth 9 to separate slow ridge mixing
from genuine multimodality on the 2-pooled-param mount. Outputs tag 'p2r'."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_nuts_pooled as rp

rp.POOL["p2r"] = rp.POOL["p2"]          # same pooling, distinct artifacts
if __name__ == "__main__":
    rp.run_tag("p2r", nwarm=2000, ndraw=2000, mtd=9, seed=3)
