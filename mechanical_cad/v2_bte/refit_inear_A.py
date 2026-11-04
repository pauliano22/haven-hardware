"""Re-score only in-ear unit A (after a shell change) and update fit_bte.json in place.
Pod and variant B rows are kept. Run cable_route.py afterwards.

    python3 refit_inear_A.py <ears_bte dir>
"""
import json
import os
import sys

import fit_bte as fb

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ears_dir = sys.argv[1]
    geo = json.load(open(os.path.join(HERE, "geometry.json")))
    meta = json.load(open(os.path.join(ears_dir, "ears.json")))
    subs = [int(k) for k in meta]
    fb.rf.tag = "inear_A"
    rows = fb.rf.evaluate(os.path.join(HERE, "bte_inear_A_R.stl"), geo["inear_A"]["com"], geo["inear_A"]["mass_g"], ears_dir, subs, crop=35.0)
    path = os.path.join(HERE, "fit_bte.json")
    out = json.load(open(path))
    by = {r["subject"]: r for r in rows}
    for rec in out:
        rec["inear"] = by[rec["inear"]["subject"]]
    json.dump(out, open(path, "w"), indent=1)


if __name__ == "__main__":
    main()
