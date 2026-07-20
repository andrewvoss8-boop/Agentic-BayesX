"""Extract Abaqus panel FEA node coords (xy.xlsx) + U3 normal mode shapes (u3.xlsx) -> out/*.npy.
Cells are comma-suffixed text. Run with a python that has openpyxl+numpy (system python3)."""
import os, numpy as np, openpyxl
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
BASE = os.path.join(REPO, "Suspended panel modal testing", "FEA results", "Output")
def tofloat(v):
    try: return float(str(v).strip().rstrip(","))
    except Exception: return None
ws = openpyxl.load_workbook(os.path.join(BASE, "xy.xlsx"), read_only=True).active
xy = []
for row in ws.iter_rows(values_only=True):
    vals = [tofloat(v) for v in row]; vals = [v for v in vals if v is not None]
    if len(vals) >= 2: xy.append(vals[:2])
xy = np.array(xy, float)
ws2 = openpyxl.load_workbook(os.path.join(BASE, "u3.xlsx"), read_only=True).active
num = []
for r in ws2.iter_rows(values_only=True):
    vals = [tofloat(v) for v in r]; vals = [v for v in vals if v is not None]
    if len(vals) > 900: num.append(vals)
L = min(len(v) for v in num); U3 = np.array([v[:L] for v in num], float)
np.save(os.path.join(OUT, "panel_fea_xy.npy"), xy)
np.save(os.path.join(OUT, "panel_fea_u3.npy"), U3)
print("extracted panel FEA: xy", xy.shape, "U3", U3.shape)
