#!/usr/bin/env python3
"""Export the demo's totals from the private reels database. Counts and rates only: no reel ids, creators, captions or quotes.
Usage: python3 tools/export_aggregates.py /path/to/data   (the folder holding reels.db, health.json, reliability.json)
Prints aggregates.json to stdout. Opens the database read-only."""
import json, sqlite3, sys, os
d = sys.argv[1]
c = sqlite3.connect("file:%s?mode=ro" % os.path.join(d, "reels.db"), uri=True)
one = lambda s: c.execute(s).fetchone()[0]
rows = lambda s: dict(c.execute(s).fetchall())
h = json.load(open(os.path.join(d, "health.json")))
rel = json.load(open(os.path.join(d, "reliability.json")))
res = rows("select verdict,count(*) from research group by 1")
rules = rows("select rule,count(*) from gate group by 1")
mode = rows("select mode,count(*) from gate group by 1")
latest = dict(c.execute("select source_folder,count(*) from reels where date(captured)=(select max(date(captured)) from reels) group by 1").fetchall())
so = rows("select agree,count(*) from second_opinion group by 1")
dec = rows("select action,count(*) from decisions group by 1")
apps = rows("select status,count(*) from applications group by 1")
stats = {"library": one("select count(*) from library"), "evidence": h.get("evidence_ok") or one("select count(*) from evidence"),
         "tech": latest.get("tech-bro", 0), "stocks": latest.get("stocks", 0), "research": one("select count(*) from research"),
         "researched_true": res.get("exists-confirmed", 0) + res.get("true", 0), "funnels": rules.get("G2", 0) + rules.get("G2b", 0),
         "falsified": res.get("false", 0), "adopt": mode.get("adopt", 0), "trial": mode.get("trial", 0),
         "second_agree": so.get(1, 0), "second_disagree": so.get(0, 0), "apps": apps,
         "decisions": {k: dec.get(k, 0) for k in ("approve", "change", "promote", "skip")}}
keep = {}
for k in ("hand_vs_gate", "second_model", "outcomes", "determinism", "links", "audit", "gold"):
    if k in rel:
        v = dict(rel[k]); [v.pop(x, None) for x in ("rows", "disagreements")]; keep[k] = v
keep["measured"] = rel.get("measured")
print(json.dumps({"stats": stats, "rules": rules, "rel": keep}, indent=1))
