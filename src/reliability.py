#!/usr/bin/env python3
"""Is the loop reliable? Measures it instead of asserting it. Writes data/reliability.json for the studio.
Usage: python3 scripts/reliability.py [--links] [--audit N]
  (always)  agreement of gate truth with the hand-carded truth, agreement with the gold set (data/gold-truth.jsonl, 100 reels),
            hand-judged-false reels that were adopted, second-model agreement, real outcomes
  --links   re-fetch the sources behind verified claims and count how many are still reachable
  --audit N blind audit: a non-Claude model (Cursor CLI) labels N sampled decisions from the evidence alone, without seeing our label
Python 3.9 compatible. No Instagram access."""
import argparse, json, math, random, re, sqlite3, subprocess, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "reliability.json"
c = sqlite3.connect(ROOT / "data" / "reels.db")
q = lambda s, a=(): c.execute(s, a).fetchall()
def wilson(k, n, z=1.96):
    if n == 0: return [0, 0]
    p = k / n; d = 1 + z * z / n
    m = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0, m - h), 3), round(min(1, m + h), 3)]
res = json.loads(OUT.read_text()) if OUT.exists() else {}
res["measured"] = time.strftime("%Y-%m-%d %H:%M")
# 1 hand truth vs gate
rows = q("""SELECT h.truth, g.truth_final FROM reels h JOIN gate g ON g.reel_id=h.id WHERE h.truth IN ('true','false')""")
pos = {"verified", "partly"}; neg = {"false", "suspicious"}
agree = sum(1 for h, g in rows if (h == "true" and g in pos) or (h == "false" and g in neg))
dis = [(h, g) for h, g in rows if not ((h == "true" and g in pos) or (h == "false" and g in neg))]
res["hand_vs_gate"] = dict(n=len(rows), agree=agree, ci=wilson(agree, len(rows)),
    note="hand-carded truth (true/false) against the gate's verdict; 'unverified' gate rows are counted as disagreement with a hand true/false",
    disagreements={f"{h}->{g}": sum(1 for x in dis if x == (h, g)) for h, g in set(dis)})
# 1b gold set: 100 labelled reels (31 hand cards + 69 agent-judged, see the header line of data/gold-truth.jsonl)
GOLD = ROOT / "data" / "gold-truth.jsonl"
if GOLD.exists():
    gold = [json.loads(l) for l in GOLD.read_text().splitlines() if l.strip()]
    hdr = next((g for g in gold if "_header" in g), {}); gold = [g for g in gold if "id" in g]
    # what a gate decision may be called by the gold label (same mapping as the blind audit, plus: false -> false|funnel, unverified -> unverifiable)
    ok = {"verified": {"reliable"}, "partly": {"partly", "unverifiable", "reliable"}, "suspicious": {"funnel", "false"},
          "false": {"false", "funnel"}, "unverified": {"unverifiable"}}
    gm = {r[0]: r[1:] for r in q("SELECT reel_id, truth_final, mode, rule FROM gate")}
    scored = [(g, gm[g["id"]]) for g in gold if g["id"] in gm]
    hit = [x for x in scored if x[0]["label"] in ok[x[1][0]]]
    bad_adopt = [g["id"] for g, m in scored if g["label"] in ("false", "funnel") and m[1] == "adopt"]
    bad_trial = [g["id"] for g, m in scored if g["label"] in ("false", "funnel") and m[1] == "trial"]
    part = lambda src: (lambda sub: dict(n=len(sub), agree=sum(1 for g, m in sub if g["label"] in ok[m[0]])))([x for x in scored if x[0]["source"] == src])
    res["gold"] = dict(n=len(scored), agree=len(hit), ci=wilson(len(hit), len(scored)), hand_cards=part("hand-card"), agent_judged=part("agent-judged"),
        false_adopted=len(bad_adopt), false_adopted_ids=bad_adopt, false_in_trial=len(bad_trial),
        h1_fired=q("SELECT COUNT(*) FROM gate WHERE rule LIKE '%+H1'")[0][0],
        disagreements=sorted("%s: gold %s, gate %s/%s %s" % (g["id"], g["label"], *m) for g, m in scored if g not in [h[0] for h in hit]),
        note="gate truth against gold labels; the gold set was also used to tune rules G2b/G3c/funnel, so the blind audit (fresh sample) is the held-out test. " + (hdr.get("_header", "")[:200]))
# 2 second model
so = q("SELECT agree, COUNT(*) FROM second_opinion WHERE model NOT LIKE 'auto%' GROUP BY 1")
n2 = sum(v for _, v in so); a2 = sum(v for k, v in so if k == 1)
res["second_model"] = dict(n=n2, agree=a2, ci=wilson(a2, n2), note="non-Claude reviewer on adopts that target a project; disagreement sends the idea to trial")
# 3 real outcomes
w = q("SELECT COUNT(*) FROM applications WHERE status='worked'")[0][0]; f = q("SELECT COUNT(*) FROM applications WHERE status='failed'")[0][0]
res["outcomes"] = dict(worked=w, failed=f, ci=wilson(w, w + f), note="tested applications only; notes written but untested are not counted")
# 4 determinism: same data in, same gate out
import hashlib
def gate_hash():
    p = subprocess.run(["python3", str(ROOT / "scripts" / "autogate.py")], capture_output=True, text=True).stdout
    return hashlib.sha1(p.encode()).hexdigest()[:10]
h1, h2 = gate_hash(), gate_hash()
res["determinism"] = dict(same=(h1 == h2), runs=2, hash=h1)
# 5 links
a = argparse.ArgumentParser(); a.add_argument("--links", action="store_true"); a.add_argument("--audit", type=int, default=0); a = a.parse_args()
if a.links:
    urls = []
    for rid, s in q("SELECT r.reel_id, r.sources FROM research r JOIN gate g ON g.reel_id=r.reel_id WHERE g.truth_final='verified' AND r.sources IS NOT NULL"):
        urls += [u for u in json.loads(s or "[]")][:2]
    urls = sorted(set(urls))[:90]
    def chk(u):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=10); return r.status
        except urllib.error.HTTPError as e: return e.code
        except Exception: return 0
    with ThreadPoolExecutor(8) as ex: st = list(ex.map(chk, urls))
    ok = sum(1 for s in st if 200 <= s < 400)
    blocked = sum(1 for s in st if s in (401, 402, 403, 406, 429))     # access refusals (paywall, bot block), not dead pages
    dead = sum(1 for s in st if s == 404 or s == 410 or s == 0)
    res["links"] = dict(n=len(urls), alive=ok, blocked=blocked, dead=dead, reachable=ok + blocked, ci=wilson(ok + blocked, len(urls)), note="sources opened by the research agents, fetched again now")
# 6 blind audit
if a.audit:
    random.seed(int(time.strftime("%Y%m%d")))           # a new sample each day; reruns on the same day repeat it
    seen = {o["id"] for o in res.get("audit", {}).get("rows", [])}        # never re-audit the previous sample
    pick = []
    for lab, where in (("verified", "g.truth_final='verified'"), ("trial", "g.mode='trial' and g.truth_final!='verified'"), ("suspicious", "g.truth_final='suspicious'")):
        ids = [r[0] for r in q("SELECT g.reel_id FROM gate g JOIN research r ON r.reel_id=g.reel_id WHERE %s" % where)] if lab != "suspicious" else [r[0] for r in q("SELECT g.reel_id FROM gate g WHERE g.truth_final='suspicious'")]
        ids = [i for i in ids if i not in seen]; random.shuffle(ids); pick += [(i, lab) for i in ids[:max(1, a.audit // 3)]]
    out = []
    for rid, lab in pick:
        l = q("SELECT creator, caption FROM library WHERE id=?", (rid,))[0]; e = q("SELECT transcript, onscreen FROM evidence WHERE id=?", (rid,))
        r = q("SELECT claim, verdict, sources, note FROM research WHERE reel_id=?", (rid,))
        ev = " ".join(((e[0][0] or "") + " " + (e[0][1] or "")).split())[:900] if e else ""
        prompt = ("Independent audit. Do not edit anything. Judge ONE saved social-media reel from this evidence only.\nCaption: %s\nSpeech and on-screen text: %s\nResearch claim: %s | research verdict: %s | sources: %s | note: %s\n"
                  "Reply with ONE line of JSON: {\"label\":\"reliable|partly|false|funnel|unverifiable\",\"why\":\"<=20 words\"}. reliable = the main claim or tool is real and sourced; funnel = comment-for-DM, income promise or password ask with no proof."
                  % (" ".join((l[1] or "").split())[:300], ev, r[0][0] if r else "-", r[0][1] if r else "-", r[0][2] if r else "-", (r[0][3] or "")[:300] if r else "-"))
        try:
            p = subprocess.run(["agent", "-p", "--mode", "ask", "--model", "gpt-5.3-codex-high", prompt], capture_output=True, text=True, timeout=240)
            j = json.loads(re.search(r"\{.*?\}", p.stdout, re.S).group(0)); out.append(dict(id=rid, ours=lab, theirs=j["label"], why=j.get("why", "")))
        except Exception as ex: out.append(dict(id=rid, ours=lab, theirs="error", why=str(ex)[:80]))
        print(rid, lab, out[-1]["theirs"], flush=True)
    map_ = {"verified": {"reliable"}, "trial": {"partly", "unverifiable", "reliable"}, "suspicious": {"funnel", "false"}}
    judged = [o for o in out if o["theirs"] != "error"]
    k = sum(1 for o in judged if o["theirs"] in map_[o["ours"]])
    res["audit"] = dict(n=len(judged), agree=k, ci=wilson(k, len(judged)), rows=out, model="gpt-5.3-codex-high",
        note="blind: the auditor never saw our label. Agreement counts 'reliable' for verified, 'partly/unverifiable/reliable' for trial, 'funnel/false' for suspicious.")
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
# one line per run, so reliability can be tracked over time (see analysis/RELIABILITY_TRACKING_PLAN.md)
snap = {"at": res["measured"]}
for k in ("hand_vs_gate", "gold", "audit", "second_model", "outcomes", "links"):
    if k in res: snap[k] = {"agree": res[k].get("agree", res[k].get("reachable", res[k].get("alive"))), "n": res[k].get("n", res[k].get("worked", 0) + res[k].get("failed", 0)), "ci": res[k].get("ci")}
snap["deterministic"] = res.get("determinism", {}).get("same")
with open(ROOT / "data" / "reliability-history.jsonl", "a") as fh: fh.write(json.dumps(snap) + "\n")
print(json.dumps({k: v for k, v in res.items() if k != "audit"}, ensure_ascii=False)[:1500])
