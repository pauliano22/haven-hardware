"""Collect shells + centre of mass for evaluate_fit.py."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
geo = json.load(open(os.path.join(HERE, "geometry.json")))
jobs = []
for tag in ("v2_nestled", "v2_nestled_fin", "v2_stacked", "v2_stacked_fin"):
    if tag in geo:
        jobs.append(dict(name=tag, stl=os.path.join(HERE, f"{tag}_shell.stl"), com=geo[tag]["com"], mass_g=geo[tag]["mass_g"]))
ref = json.load(open(os.path.join(HERE, "ref_block.json")))
jobs.append(dict(name="block_reference", stl=ref["stl"], com=ref["com"], mass_g=ref["mass_g"]))
json.dump(jobs, open(os.path.join(HERE, "fit_jobs.json"), "w"), indent=1)
print([j["name"] for j in jobs])
