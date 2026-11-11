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
 dict(id="DfAhxORzj09", who="@petergriffin.ai", quote="someone open-sourced the Claude job hunter that got him hired", took="An open-source tool that scores job listings against your CV and skips weak matches. The project exists on GitHub; the video's popularity figure was only partly confirmed.", used="Idea for a job-search helper, tried on a small scale first.", verdict="partly-true", gate={"truth": "partly"}, sources=["https://github.com/santifer/career-ops"]),
 dict(id="DfctammtEkq", who="@petergriffin.ai", quote="Claude just hacked the stock market with this one free skill", took="Nothing to use as a trading method. The free skill pack is real, but the 'hacked the stock market' promise is hype and the post is a sales funnel.", used="Rejected for trading; kept as an example of a real tool inside a funnel.", verdict="true", gate={"truth": "partly"}, sources=["https://github.com/Jakeschincariol/day-trader-skill"]),
 dict(id="De7z-exNXI5", who="@arellano_dev", quote="Stanford just gave away a Jarvis for free and it lives on your computer.", took="A free open-source assistant that runs on your own computer. The project is real, with an open licence and about 12,700 stars, but the post pushes a one-line install that pipes a web script into the shell, which is risky.", used="Read the code before installing anything like this.", verdict="exists-confirmed", gate={"truth": "partly"}, sources=["https://github.com/open-jarvis/OpenJarvis"]),
 dict(id="DfAqoJft6Bl", who="@madebyossyy", quote="motion graphics like this can be made without even opening After Effects", took="Describe a motion graphic to an AI and get the video. The product page confirms the feature exists, but the post is a partner advert.", used="Noted as a possible tool for making short videos.", verdict="partly-true", gate={"truth": "partly"}, sources=["https://higgsfield.ai/blog/higgsfield-katana"]),
]
traces = [
 dict(id="DfAhxORzj09", creator="petergriffin.ai", folder="Jobs", caption="Claude Can Now Apply for Jobs for You", speech="someone open-sourced the Claude job hunter that got him hired", screen="", claim="Career-Ops is an open-source Claude job-hunting workflow that scores jobs out of 5 and skips the weak ones.", verdict="partly-true", conf="high", sources=["https://github.com/santifer/career-ops"], note="The repository exists and works as described. The star count quoted in the video was only partly confirmed.", use="Try it on a few real job listings before relying on it.", flags=["funnel"], gate=dict(truth="suspicious", mode="none", rule="G2", project="", score=0), second={}, app={}, plain="A real open-source job-hunting helper for the AI tool Claude. The project exists, but the post is a comment-for-the-link funnel, so it is flagged and not used directly."),
 dict(id="DfctammtEkq", creator="petergriffin.ai", folder="Stocks", caption="Claude Just Hacked the Stock Market With 11 Free Trading Skills", speech="Claude just hacked the stock market with this one free skill", screen="", claim="A free pack of 11 trading add-ons for Claude (chart scanner, news, stops, a 10,000-run simulator) exists.", verdict="true", conf="high", sources=["https://github.com/Jakeschincariol/day-trader-skill"], note="The repository exists and matches the description. Its own page makes no profit claims.", use="Do not install or trade on this.", flags=["funnel"], gate=dict(truth="partly", mode="trial", rule="G3b", project="Trading", score=9), second={}, app=dict(status="rejected", outcome="Refused: a real tool inside a sales-funnel post. Do not install it or trade on it.", idea=""), plain="A free set of 11 trading add-ons for Claude. The project is real, but the headline about hacking the stock market is hype: it does not make money by itself."),
 dict(id="De7z-exNXI5", creator="arellano_dev", folder="Tech bro", caption="(no caption)", speech="Stanford just gave away a Jarvis for free and it lives on your computer.", screen="", claim="OpenJarvis is a free assistant that runs on your own computer.", verdict="exists-confirmed", conf="high", sources=["https://github.com/open-jarvis/OpenJarvis"], note="The repository exists with an Apache-2.0 licence, about 12,700 stars and a recent update. The video recommends a one-line install that pipes a web script into the shell.", use="Read the code and the install script before running anything.", flags=["funnel", "pipe-to-shell"], gate=dict(truth="partly", mode="trial", rule="G3b", project="Assistant", score=14), second={}, app={}, plain="A free open-source assistant that runs on your own computer. The project is real (about 12,700 stars, open licence), but the post pushes a one-line install that runs a web script blindly, so it is flagged for testing, not for trust."),
 dict(id="DfIuvawOTza", creator="chase.h.ai", folder="Tech bro", caption="Comment “Jarvis” to get my Claude agentic OS", speech="This dashboard is completely customized to what I think is important.", screen="", claim="A custom dashboard over AI coding tools, with a voice mode that routes requests to different models.", verdict="unverifiable", conf="medium", sources=[], note="Nothing in the video can be checked, and the comment-to-get-it pattern is a sales funnel.", use="", flags=["funnel"], gate=dict(truth="suspicious", mode="none", rule="G2", project="", score=0), second={}, app={}, plain="A creator shows a personal dashboard on top of AI coding tools and asks you to comment “Jarvis” to get it. Nothing in the video can be checked and the pattern is a sales funnel. The design ideas can still be borrowed."),
 dict(id="DfAqoJft6Bl", creator="madebyossyy", folder="Tech bro", caption="Higgsfield Katana is a Video Editor GAME CHANGER", speech="motion graphics like this can be made without even opening After Effects", screen="", claim="Higgsfield Katana lets you make motion graphics by describing them to an AI.", verdict="partly-true", conf="medium", sources=["https://higgsfield.ai/blog/higgsfield-katana"], note="The product page confirms the feature. The post is a partner advert.", use="Possible tool for short videos.", flags=["funnel"], gate=dict(truth="suspicious", mode="none", rule="G2", project="", score=0), second={}, app={}, plain="A partner advert for a video editor that says motion graphics can be made by describing them to an AI. The product page confirms the feature exists, but it is an advert."),
]
rnd = random.Random(3)
pool = [[f"demo-{rnd.randint(100, 999)}", o] for o, k in (("refused", 14), ("none", 8), ("trial", 8), ("adopt", 8)) for _ in range(k)]
ledger = [dict(t="2026-11-11 09:40", reel="DfctammtEkq", status="rejected", text="Refused: a real tool inside a sales-funnel post."), dict(t="2026-11-11 09:12", reel="De7z-exNXI5", status="proposed", text="Read the code and install script before running anything."), dict(t="2026-11-10 18:03", reel="DfAhxORzj09", status="proposed", text="Try on a few real job listings first."), dict(t="2026-11-10 17:41", reel="DfAqoJft6Bl", status="proposed", text="Possible tool for short videos.")]
data = dict(built="demo build", stats=agg["stats"], rules=agg["rules"], rel=agg["rel"], picks=dict(look=look, say=say), traces=traces, ledger=ledger, pool=pool, demo=True)
tpl = (R / "template.html").read_text()
(R / "docs").mkdir(exist_ok=True)
(R / "docs" / "index.html").write_text(tpl.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False)))
print("wrote docs/index.html")
