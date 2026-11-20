#!/usr/bin/env python3
"""Autonomous gate: researched evidence -> final truth -> where to apply it. No human approval step. No network, no tokens.

Usage: python3 scripts/autogate.py [--write]    (dry run prints the counts and the apply queue)

For every reel in `library` it combines the research verdict (table `research`), the claim triage
(`verification`) and the vetting card truth (`reels`) into one auditable decision in table `gate`:

  truth_final  verified | partly | false | suspicious | unverified
  mode         adopt  (verified: apply it)
               trial  (partly or saved idea: apply in a sandbox or branch, keep only if the test passes)
               none   (false, suspicious, unverified with nothing to test)
  rule         the rule that fired, so any decision can be re-derived and audited

Rules, in order (first match wins):
  G1 research false with a source                  -> false / none
  G2 funnel or income claim and no source-backed 'true' -> suspicious / none
  G3 research true|exists-confirmed, a source, confidence not low -> verified / adopt
  G3b same, but the reel carries a funnel or risk flag -> partly / trial (found by the reliability audit: hand cards had called these false)
  G3c same as G3, but the claim is advice, a heuristic or an opinion (research note admits it is untested, unclear, hype ...)
      -> partly / trial (2026-11-11: 3 of 8 sampled 'verified' were called 'partly' by the blind auditor; 'the tool exists' is not 'the advice works')
  G2b funnel flag only (no key/cookie/not-found flag), research partly|partly-true with a source and confidence not low
      -> partly / trial (2026-11-11: the thing is real, the reel is a funnel; 8 gold-set reels were wrongly 'suspicious')
  G4 research partly|partly-true with a source     -> partly / trial
  G5 research saved-idea|idea-only and relevance >= 12 -> unverified / trial
  G6 hand-carded truth true with no research       -> verified / adopt (only if no risk flags)
  G7 everything else                               -> unverified / none
Learning rules run before G1-G7 (outcomes come from `apply.py outcome`):
  F2 the idea worked in use -> verified / adopt     F4 it failed -> partly / none (never queued again)
  H1 safety net: a reel whose hand card says false is never adopted (adopt -> trial, rule gets '+H1'); counted in reliability.py
  F1 a creator with 2+ failed trials and no worked one -> their unproven reels go to none
  F3 a rule (G4/G5) whose trials fail >= 50% over 4+ outcomes is switched off until it recovers

Then, for mode adopt|trial and a project score >= 10 (relevance.PROJECTS), it writes an `applications` row
(status 'proposed', idea from research.use_note) unless the reel already has one, and writes the per-project
queue analysis/apply-queue/<project>.md for Raphael, Claude and Cursor to pick up. The gate never edits reels.truth,
never writes to Instagram, and a failed trial is recorded through scripts/apply.py outcome so it feeds back.
Python 3.9 compatible.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from relevance import PROJECTS, score  # noqa: E402

DB = ROOT / "data" / "reels.db"
RISK = {"funnel", "asks:password", "asks:cookies", "asks:api key", "named-thing-not-found"}
# G3c: words the research agents use when the thing is real but the reel's advice or headline is not proven. Conservative: only the
# research note is searched (the agent's own admission), plus a short list of advice phrasings in the claim.
CAVEAT = re.compile(r"untested|unproven|not (?:shown|tested|verified|checked|backed|confirmed|independently)|could not confirm|no evidence|"
                    r"no independent|opinion|subjective|hyperbole|hype\b|overstated|oversold|unclear|anecdot|creator'?s own|marketing|"
                    r"\bnot free\b|depends on", re.I)
ADVICE = re.compile(r"\bbest way\b|\bshould\b|\bbetter than\b|\bso good\b|\bgood way\b|\bpairs (?:well|perfectly)\b|\boutperform|\bprecise\b", re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    con = sqlite3.connect(DB)
    now = time.strftime("%Y-%m-%d %H:%M")
    rows = con.execute("""SELECT l.id, l.creator, COALESCE(l.caption,''), COALESCE(e.transcript,''), COALESCE(e.onscreen,''),
                          r.verdict, r.confidence, r.sources, r.use_note, r.note, v.flags, h.truth, r.claim
                          FROM library l LEFT JOIN evidence e ON e.id=l.id
                          LEFT JOIN research r ON r.reel_id=l.id
                          LEFT JOIN verification v ON v.reel_id=l.id
                          LEFT JOIN reels h ON h.id=l.id""").fetchall()
    out, queue = [], {}
    existing = {r[0] for r in con.execute("SELECT reel_id FROM applications")}
    # LEARN: real outcomes (scripts/apply.py outcome worked|failed) feed back into the rules.
    outcome = {r[0]: r[1] for r in con.execute(
        "SELECT reel_id, status FROM applications WHERE status IN ('worked','failed')")}
    creator_of = {r[0]: r[1] for r in con.execute("SELECT id, creator FROM library")}
    gate_before = {}
    if con.execute("SELECT 1 FROM sqlite_master WHERE name='gate'").fetchone():
        gate_before = {r[0]: r[1] for r in con.execute("SELECT reel_id, rule FROM gate")}
    second = {}
    if con.execute("SELECT 1 FROM sqlite_master WHERE name='second_opinion'").fetchone():
        second = {r[0]: r[1] for r in con.execute("SELECT reel_id, agree FROM second_opinion")}
    cr = {}
    rl = {}
    for rid, st in outcome.items():
        c = cr.setdefault(creator_of.get(rid), [0, 0])
        c[0 if st == "worked" else 1] += 1
        r_ = rl.setdefault(gate_before.get(rid, "?"), [0, 0])
        r_[0 if st == "worked" else 1] += 1
    burned = {c for c, (w, f) in cr.items() if f >= 2 and w == 0}          # F1: creator whose ideas keep failing
    weak_rules = {r for r, (w, f) in rl.items() if w + f >= 4 and f / (w + f) >= 0.5}  # F3: a rule that mostly fails
    for rid, creator, cap, tr, on, verdict, conf, srcs, use, note, flags, hand, claim in rows:
        src = bool(json.loads(srcs or "[]")) if srcs else False
        risk = bool(RISK & set(json.loads(flags or "[]")))
        text = (cap + " " + tr + " " + on).lower()
        sc = {p: score(text, w)[0] for p, w in PROJECTS.items()}
        proj, best = max(sc.items(), key=lambda kv: kv[1])
        if outcome.get(rid) == "worked":
            t, mode, rule = "verified", "adopt", "F2"                       # proved in use
        elif outcome.get(rid) == "failed":
            t, mode, rule = "partly", "none", "F4"                          # tried and failed: stop queueing
        elif creator in burned and not (verdict in ("true", "exists-confirmed") and src):
            t, mode, rule = "unverified", "none", "F1"
        elif verdict == "false" and src:
            t, mode, rule = "false", "none", "G1"
        elif (set(json.loads(flags or "[]")) & RISK) == {"funnel"} and verdict in ("partly", "partly-true") and src and conf != "low":
            t, mode, rule = "partly", "trial", "G2b"        # real but a funnel: sandbox only
        elif risk and not (verdict in ("true", "exists-confirmed") and src):
            t, mode, rule = "suspicious", "none", "G2"
        elif risk and verdict in ("true", "exists-confirmed") and src:
            t, mode, rule = "partly", "trial", "G3b"        # the thing exists, but the reel is a funnel: sandbox only
        elif verdict in ("true", "exists-confirmed") and src and conf != "low" and (CAVEAT.search(note or "") or ADVICE.search(claim or "")):
            t, mode, rule = "partly", "trial", "G3c"        # real thing, unproven advice: sandbox only
        elif verdict in ("true", "exists-confirmed") and src and conf != "low":
            t, mode, rule = "verified", "adopt", "G3"
        elif verdict in ("partly", "partly-true") and src and "G4" not in weak_rules:
            t, mode, rule = "partly", "trial", "G4"
        elif verdict in ("saved-idea", "idea-only") and best >= 12 and "G5" not in weak_rules:
            t, mode, rule = "unverified", "trial", "G5"
        elif hand == "true" and not risk:
            t, mode, rule = "verified", "adopt", "G6"
        else:
            t, mode, rule = "unverified", "none", "G7"
        if mode == "adopt" and hand == "false":                              # H1: never adopt what a hand card called false
            mode, rule = "trial", rule + "+H1"
        if mode == "adopt" and second.get(rid) == 0:                         # R2: the other model disagrees
            mode, rule = "trial", rule + "+R2"
        target = proj if (mode != "none" and best >= 10) else ""
        out.append((rid, t, mode, rule, target, round(best, 1), now))
        if target:
            queue.setdefault(target, []).append((best, rid, creator, t, mode, (use or note or cap)[:220].replace("\n", " ")))
    print("gate decisions:", len(out), "| burned creators:", sorted(burned), "| weak rules:", sorted(weak_rules))
    from collections import Counter
    print(Counter((o[1], o[2]) for o in out))
    print("apply targets:", {p: len(v) for p, v in queue.items()})
    if not a.write:
        return 0
    con.execute("""CREATE TABLE IF NOT EXISTS gate (reel_id TEXT PRIMARY KEY, truth_final TEXT, mode TEXT, rule TEXT,
                   project TEXT, score REAL, decided TEXT)""")
    con.executemany("INSERT OR REPLACE INTO gate VALUES (?,?,?,?,?,?,?)", out)
    new_apps = 0
    for proj, items in queue.items():
        for best, rid, creator, t, mode, idea in items:
            if rid in existing:
                continue
            con.execute("INSERT INTO applications (reel_id, project, idea, status, outcome, created, updated) VALUES (?,?,?,?,?,?,?)",
                        (rid, proj, "[%s] %s" % (mode, idea), "proposed", "", now, now))
            new_apps += 1
    con.commit()
    qd = ROOT / "analysis" / "apply-queue"
    qd.mkdir(exist_ok=True)
    for proj, items in queue.items():
        items.sort(reverse=True)
        lines = ["# Apply queue: %s (generated %s by scripts/autogate.py)" % (proj, now), "",
                 "adopt = verified, use it. trial = unproven or partly true, test in a sandbox or branch first and record the result with `scripts/apply.py outcome`. "
                 "False, suspicious and unverified-with-nothing-to-test reels never appear here.", "",
                 "| reel | @creator | truth | mode | idea / how to use |", "|---|---|---|---|---|"]
        for best, rid, creator, t, mode, idea in items[:40]:
            lines.append("| %s | @%s | %s | %s | %s |" % (rid, creator, t, mode, idea.replace("|", "/")))
        (qd / (re.sub(r"[^a-z0-9]+", "-", proj.lower()).strip("-") + ".md")).write_text("\n".join(lines) + "\n")
    print("gate table written; %d new application rows" % new_apps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
