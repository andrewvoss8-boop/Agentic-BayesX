#!/usr/bin/env python3
"""Thin wrapper: run the REUSED mech_gates.py (V1-V5) inside OUR workspace. femdamp sets F.WS -> our WS and
puts our code dir first, so mech_gates writes out/mech_gates.json + data/packages here. Resumable."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femdamp  # noqa: F401  (sets F.WS = our workspace, redirects femlib IO)
import mech_gates  # noqa: F401  (executes V1-V5 at import, in our workspace)
