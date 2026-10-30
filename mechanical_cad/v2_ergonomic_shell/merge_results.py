"""Rebuild fit_results.json from an evaluate_fit.py log plus extra rows (used when a long run
was cut off and only the missing ear/shell pairs were re-run)."""
import ast, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
names = {"ref_block_bud_in_ear_frame.stl": "block_reference"}
out = {}
for line in open(sys.argv[1]):
    if "{'subject'" not in line:
        continue
    f, d = line.split(" ", 1)
    tag = names.get(f, f.replace("_shell.stl", ""))
    out.setdefault(tag, []).append(ast.literal_eval(d.strip()))
for extra in sys.argv[2:]:
    tag, path = extra.split("=")
    have = {r["subject"] for r in out.get(tag, [])}
    out.setdefault(tag, []).extend(r for r in json.load(open(path)) if r["subject"] not in have)
json.dump(out, open(os.path.join(HERE, "fit_results.json"), "w"), indent=1)
print({k: len(v) for k, v in out.items()})
