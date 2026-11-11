#!/usr/bin/env python3
"""Builds docs/index.html from template.html + aggregates.json + invented demo content.
Nothing here comes from a real person's video: creators, captions, quotes and pictures are made up.
Usage: python3 build_demo.py"""
import base64, json, random
from pathlib import Path
R = Path(__file__).resolve().parent
agg = json.loads((R / "aggregates.json").read_text())

def svg(kind):
    bg, ln = "#0b1220", "#22304f"
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 300"><rect width="640" height="300" fill="{bg}"/>']
    rnd = random.Random(kind)
    if kind == "graph":
        pts = [(90, 150), (220, 80), (230, 220), (360, 140), (490, 80), (520, 215)]
        for a, b in [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (3, 5)]:
            o.append(f'<line x1="{pts[a][0]}" y1="{pts[a][1]}" x2="{pts[b][0]}" y2="{pts[b][1]}" stroke="{ln}" stroke-width="3"/>')
        for i, (x, y) in enumerate(pts):
            col = ["#38bdf8", "#a78bfa", "#f5a524", "#34d399", "#f472b6", "#2dd4bf"][i]
            o.append(f'<circle cx="{x}" cy="{y}" r="26" fill="{col}" opacity=".18"/><circle cx="{x}" cy="{y}" r="14" fill="{col}"/>')
        o.append(f'<rect x="548" y="40" width="80" height="220" rx="10" fill="#121c31" stroke="{ln}"/>')
    elif kind == "matrix":
        for r in range(6):
            for c in range(9):
                v = rnd.random(); col = "#6d5bd6" if v > .25 else "#f87171"
                o.append(f'<rect x="{40 + c * 50}" y="{30 + r * 40}" width="44" height="34" rx="5" fill="{col}" opacity="{.35 + v * .6:.2f}"/>')
    elif kind == "steps":
        for i, (x, col) in enumerate([(70, "#f87171"), (250, "#34d399"), (430, "#38bdf8")]):
            o.append(f'<rect x="{x}" y="105" width="140" height="70" rx="12" fill="#121c31" stroke="{col}" stroke-width="2"/><rect x="{x + 10}" y="76" width="46" height="20" rx="10" fill="{col}"/>')
            if i < 2: o.append(f'<line x1="{x + 140}" y1="140" x2="{x + 180}" y2="140" stroke="#34d399" stroke-width="3"/>')
    elif kind == "ledger":
        for r in range(7):
            y = 30 + r * 36; hl = r == 3
            o.append(f'<rect x="40" y="{y}" width="560" height="30" rx="8" fill="#121c31" stroke="{"#f87171" if hl else ln}"/><rect x="56" y="{y + 11}" width="{120 + rnd.randint(0, 160)}" height="8" rx="4" fill="#56627d"/><rect x="520" y="{y + 7}" width="64" height="16" rx="8" fill="#f5a524" opacity=".5"/>')
    elif kind == "funnel":
        o.append('<path d="M150 60 L490 60 L380 190 L260 190 Z" fill="none" stroke="#38bdf8" stroke-width="3"/><rect x="290" y="190" width="60" height="50" fill="none" stroke="#38bdf8" stroke-width="3"/>')
        for x, y in [(210, 30), (300, 20), (400, 34), (260, 100), (360, 120)]:
            o.append(f'<rect x="{x}" y="{y}" width="40" height="18" rx="5" fill="#38bdf8" opacity=".8"/>')
    elif kind == "radar":
        o.append('<circle cx="320" cy="150" r="120" fill="none" stroke="#f5a524"/><circle cx="320" cy="150" r="80" fill="none" stroke="#f5a52455"/><circle cx="320" cy="150" r="40" fill="none" stroke="#f5a52455"/><path d="M320 150 L430 90 A120 120 0 0 1 440 150 Z" fill="#f5a52444"/>')
        for x, y in [(270, 100), (380, 120), (350, 200), (260, 180)]:
            o.append(f'<circle cx="{x}" cy="{y}" r="6" fill="#f5a524"/>')
    elif kind == "timeline":
        for i in range(5):
            o.append(f'<rect x="{40 + i * 60}" y="{60 + (i % 3) * 30}" width="{150 + i * 10}" height="22" rx="5" fill="{["#38bdf8", "#a78bfa", "#f5a524", "#34d399", "#f472b6"][i]}" opacity=".8"/>')
        o.append('<line x1="300" y1="30" x2="300" y2="260" stroke="#f87171" stroke-width="3"/><path d="M290 30 L310 30 L300 44 Z" fill="#f87171"/>')
    o.append("</svg>")
    return "data:image/svg+xml;base64," + base64.b64encode("".join(o).encode()).decode()

look = [
 dict(id="demo-L1", who="@example_studio", img="graph", took="A map of helpers drawn as glowing dots joined by lines, with a side panel that shows details when you pick one.", used="The map at the top of this page: each stage is a dot, and clicking one opens its details below.", claim="An invented example. In the real system this card links to the saved video."),
 dict(id="demo-L2", who="@example_studio", img="matrix", took="A colour grid that scores several AI models against several tests; the weakest square opens its details.", used="Idea for showing how each audited video scored.", claim="An invented example."),
 dict(id="demo-L3", who="@example_flows", img="steps", took="Each step has a numbered badge and a clock time, and steps are joined by green lines that light up as they pass.", used="'Follow one video, step by step'.", claim="Imagine the video also promised a $5,000 income. That is a sales pitch with no proof, so the claim is rejected and only the design is kept."),
 dict(id="demo-L4", who="@example_ops", img="ledger", took="A running list of events where one row is highlighted and each row carries a small status tag.", used="The 'What the system just did' list.", claim="An invented example."),
 dict(id="demo-L5", who="@example_flows", img="funnel", took="A funnel that scores items as they drop in, and numbers that count up from zero.", used="The Collect scene and the counting numbers on every stage.", claim="An invented example."),
 dict(id="demo-L6", who="@example_flows", img="radar", took="A radar that sweeps round and pings results as it passes.", used="The Verify scene.", claim="An invented example."),
 dict(id="demo-L7", who="@example_edit", img="timeline", took="Colour-coded, labelled cursors moving over a timeline that has a moving playhead.", used="The helpers moving over the map, and the schedule timeline.", claim="An invented example."),
]
for it in look: it["img"] = svg(it["img"])
say = [
 dict(id="demo-S1", who="@example_quant", quote="If it only works at one exact setting, that is luck, not an edge.", took="Before trusting a trading test, shuffle the order of the trades, try it on data it has not seen, and nudge the settings.", used="A checklist for testing trading ideas.", verdict="true", gate={"truth": "verified"}, sources=["https://en.wikipedia.org/wiki/Walk_forward_optimization"]),
 dict(id="demo-S2", who="@example_ai", quote="Use the cheap model for the easy jobs and the strong one for planning.", took="Route work by difficulty to save money without losing quality. A price gap of about 40 times between small and large models is checked on the vendor's price page.", used="How an assistant chooses which AI model to call.", verdict="true", gate={"truth": "verified"}, sources=["https://www.anthropic.com/pricing"]),
 dict(id="demo-S3", who="@example_dev", quote="The assistant can turn a lamp blue when it needs you.", took="Coding assistants have built-in triggers that fire when they wait for you or finish. They can drive a smart lamp.", used="A small desk-lamp helper.", verdict="exists-confirmed", gate={"truth": "verified"}, sources=["https://docs.anthropic.com/en/docs/claude-code/hooks"]),
 dict(id="demo-S4", who="@example_study", quote="Even the citation checker misses some fake sources, so open each one yourself.", took="Always open the cited passage; a checker is a first filter, not proof.", used="A rule in the study notes.", verdict="partly-true", gate={"truth": "partly"}, sources=[]),
]
traces = [
 dict(id="demo-001", creator="example_design", folder="Tech bro", caption="This free add-on removes the 'AI-made' look from your app.", speech="It finds the purple gradients and emoji everywhere, shows you a plan, then fixes it in nine passes.", screen="before / after screenshots", claim="A free add-on finds machine-made design habits and fixes them in nine steps.", verdict="exists-confirmed", conf="high", sources=["https://github.com/"], note="The project exists, has an open licence and recent updates.", use="Try it on one screen and compare before and after.", flags=[], gate=dict(truth="verified", mode="adopt", rule="G3", project="Design", score=14), second=dict(agree=1, model="independent AI", note="The project exists and is maintained; trying it on one screen is a low-risk step."), app=dict(status="used", outcome="Tried on one screen; the result looked less generic.", idea=""), plain="A free add-on that finds design habits that make an app look machine-made and fixes them in steps. The project exists and is popular."),
 dict(id="demo-002", creator="example_quant", folder="Stocks", caption="Three checks before you trust any backtest.", speech="Shuffle the trades, test on data the model has never seen, then nudge every setting. A real edge is a plateau, not a spike.", screen="MONTE CARLO / WALK-FORWARD / SENSITIVITY", claim="Three stress tests (shuffling, walk-forward, sensitivity) separate luck from edge.", verdict="true", conf="high", sources=["https://en.wikipedia.org/wiki/Walk_forward_optimization"], note="Standard methods in quantitative finance.", use="Add the three checks to the trading test checklist.", flags=[], gate=dict(truth="verified", mode="adopt", rule="G3", project="Trading", score=21), second=dict(agree=1, model="independent AI", note="Standard, well documented methods."), app=dict(status="worked", outcome="Added to the checklist; it caught one overfitted idea.", idea=""), plain="Three checks to run before trusting a trading test: shuffle the trades, test on unseen periods, nudge the settings. These are standard, sound methods."),
 dict(id="demo-003", creator="example_getrich", folder="Stocks", caption="6 AI bots turned $89 into $55,698 while I slept. Comment BOT for the guide.", speech="Someone gave the most powerful AI eighty-nine dollars and by morning it had made almost fifty-five thousand. Comment BOT.", screen="a dashboard with a rising balance", claim="Six AI bots turned $89 into $55,698 overnight.", verdict="unverifiable", conf="low", sources=[], note="No audited record, no source, and an unaudited screenshot.", use="", flags=["funnel"], gate=dict(truth="suspicious", mode="none", rule="G2", project="", score=0), second={}, app={}, plain="Claims that six AI trading bots turned $89 into $55,698 overnight. There is no proof, and the post asks you to comment to get the guide, which is a classic sales funnel. Rejected."),
 dict(id="demo-004", creator="example_ai", folder="Tech bro", caption="Stop sending your best model to rename variables.", speech="Pick the model by the job, not by the brand. The small one is about forty times cheaper.", screen="a price table", claim="The smallest model costs about 40 times less than the largest.", verdict="true", conf="high", sources=["https://www.anthropic.com/pricing"], note="The vendor's price page shows the gap.", use="Route easy jobs to the small model.", flags=[], gate=dict(truth="verified", mode="trial", rule="G3+R2", project="Assistant", score=12), second=dict(agree=0, model="independent AI", note="The price gap is real, but quality on each job should be tested first."), app=dict(status="proposed", outcome="", idea="Route easy jobs to the small model, test quality first."), plain="Use cheaper AI models for easy jobs and the strongest for hard ones. The price gap is real, so the idea goes to a small test before it is relied on."),
 dict(id="demo-005", creator="example_dev", folder="Tech bro", caption="My lamp turns blue when my coding assistant needs me.", speech="Blue means I need you, green means I am done. The assistant has triggers for both.", screen="a lamp on a desk", claim="Coding assistants have built-in triggers that can drive a smart lamp.", verdict="exists-confirmed", conf="high", sources=["https://docs.anthropic.com/en/docs/claude-code/hooks"], note="The documented trigger events exist.", use="Build the lamp helper.", flags=[], gate=dict(truth="verified", mode="adopt", rule="G3", project="Assistant", score=11), second=dict(agree=1, model="auto", note="No money or live-risk claim; the source confirms the triggers."), app=dict(status="proposed", outcome="", idea="Wire a lamp to the triggers."), plain="A smart lamp that turns blue when the AI coding tool is waiting for you. The built-in triggers that make this possible are real."),
 dict(id="demo-006", creator="example_takes", folder="Stocks", caption="Every time a tech boss has an affair, the stock soars.", speech="Look at these three companies. Are you seeing a pattern?", screen="three rising charts", claim="Stocks rise after tech CEOs' affairs.", verdict="false", conf="high", sources=["https://en.wikipedia.org/wiki/Survivorship_bias"], note="Three hand-picked winners and no comparison group.", use="", flags=[], gate=dict(truth="false", mode="none", rule="G1", project="", score=0), second={}, app={}, plain="Claims that stocks soar when tech bosses have affairs. It picks a few winners and ignores everyone else, so it proves nothing. Rejected."),
]
rnd = random.Random(3)
pool = [[f"demo-{rnd.randint(100, 999)}", o] for o, k in (("refused", 14), ("none", 8), ("trial", 8), ("adopt", 8)) for _ in range(k)]
ledger = [dict(t="2026-11-11 09:40", reel="demo-002", status="worked", text="Added to the checklist; it caught one overfitted idea."), dict(t="2026-11-11 09:12", reel="demo-001", status="used", text="Tried on one screen."), dict(t="2026-11-10 18:03", reel="demo-004", status="proposed", text="Route easy jobs to the small model, test quality first."), dict(t="2026-11-10 17:41", reel="demo-005", status="proposed", text="Wire a lamp to the triggers.")]
data = dict(built="demo build", stats=agg["stats"], rules=agg["rules"], rel=agg["rel"], picks=dict(look=look, say=say), traces=traces, ledger=ledger, pool=pool, demo=True)
tpl = (R / "template.html").read_text()
(R / "docs").mkdir(exist_ok=True)
(R / "docs" / "index.html").write_text(tpl.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False)))
print("wrote docs/index.html")
