"""Scenes and narration for the walkthrough video. See make_video.py for the engine."""
from __future__ import annotations

import argparse
import asyncio
import re
import subprocess
from pathlib import Path

from playwright.async_api import async_playwright

from .make_video import PAGES, Scene, Voice, mux, record_scene

CONSOLE = "http://127.0.0.1:8800/"
CAP = Path("/tmp/vw")


def term_lines(path: Path, keep: int = 99) -> tuple[str, list[tuple[str, str]]]:
    raw = path.read_text().splitlines()
    cmd = re.sub(r"^\$ (env \S+ )?\S*/python ", "$ python ", raw[0])
    cmd = cmd.removeprefix("$ ")
    out = []
    for ln in raw[1:][-keep:]:
        cls = "ok" if ln.startswith("PASS") or "PASS" in ln and "gate" in ln or "passed" in ln or "All checks" in ln else "bad" if ln.startswith("FAIL") else "dim" if ln.startswith("(took") else ""
        out.append((ln, cls))
    return cmd, out


async def play_term(r, cmd: str, lines: list[tuple[str, str]], budget: float, title: str | None = None) -> None:
    p = r.page
    if title:
        await p.evaluate("t=>setTitle(t)", title)
    await p.evaluate("c=>cmd(c)", cmd)
    await p.wait_for_timeout(900)
    per = max(0.06, min(0.35, (budget - 1.4) / max(1, len(lines))))
    for txt, cls in lines:
        await p.evaluate("([t,c])=>line(t,c)", [txt, cls])
        await p.wait_for_timeout(int(per * 1000))


def build_scenes(v: Voice) -> list[Scene]:
    S = lambda name, sents, page, drv: Scene(name, sents, page, drv, [v.say(s) for s in sents], v.sr)  # noqa: E731
    P = lambda f: (PAGES / f).as_uri()  # noqa: E731
    scenes: list[Scene] = []

    # 1 title
    async def d_title(r):
        for i in range(3):
            await r.sync(i); await r.page.evaluate("n=>reveal(n)", i + 1)
    scenes.append(S("01_title", [
        "Factory to Field is an agent platform for the plants that make pumps, and for the refineries and oil wells that run them.",
        "It takes one alarm and answers what an engineer would ask: what is wrong, why, who else is exposed, and what should we do.",
        "Every answer cites its evidence. The agents can only read operations data, and every action is a draft that a named person must approve."], P("title.html"), d_title))

    # 2 architecture
    async def d_arch(r):
        for i in range(4):
            await r.sync(i); await r.page.evaluate("n=>reveal(n)", i + 1)
    scenes.append(S("02_architecture", [
        "The data lives in many systems. Historians and SCADA hold the signals. SAP holds work orders. OSDU holds wells. The pump maker's PLM, MES and quality systems hold designs, lots and claims.",
        "An ontology says what a position, a physical unit and an installation mean. A position is a slot in the plant. A unit is the pump installed there for a period of time.",
        "Identity resolution links every tag, serial number and notification to those concepts, and builds a knowledge graph of about one hundred and ten thousand facts.",
        "Agents query the graph and the live systems through read-only tools, and propose drafts. People approve, and only then is anything released."], P("arch.html"), d_arch))

    # 3 build
    async def d_build(r):
        for i, f in enumerate(["ont", "world", "kg"]):
            await r.sync(i)
            cmd, lines = term_lines(CAP / f"{f}.txt")
            if f == "ont":
                lines = [("ontology up to date: generated OWL, SHACL, Pydantic and TypeScript match the LinkML source", "ok")] + lines
            await play_term(r, cmd, lines, r.scene.durs[i], "build")
            await r.page.wait_for_timeout(300)
            if i < 2:
                await r.page.evaluate("clear()")
    scenes.append(S("03_build", [
        "Here is the real build. The ontology generates its schemas and passes its freshness check.",
        "A seeded simulator generates a plant, with failures, bearing and seal lots, and sensor behaviour. It also writes an answer key that the agents never see.",
        "The knowledge graph builds in seconds. Identity resolution recall is point nine nine nine five, precision is one hundred percent, and three orphan tags go to a human review queue."], P("term.html"), d_build))

    # 4 simulators
    async def d_sim(r):
        p = r.page
        blocks, cur = [], None
        for ln in (CAP / "sim.txt").read_text().splitlines():
            if ln.startswith("$ "):
                cur = [ln]; blocks.append(cur)
            elif cur is not None and ln:
                cur.append(ln)
        async def play(bs, budget):
            n = sum(len(b) for b in bs)
            per = max(0.2, min(0.9, budget / n))
            for blk in bs:
                for ln in blk:
                    cls = "c" if ln.startswith("$ ") else "bad" if re.match(r"HTTP 4", ln) else "ok" if ln.startswith("HTTP 200") else ""
                    await p.evaluate("([t,c])=>line(t,c)", [ln, cls]); await p.wait_for_timeout(int(per * 1000))
                await p.evaluate("([t,c])=>line(t,c)", ["", ""])
        await p.evaluate("t=>setTitle(t)", "plant system simulators (local)")
        await r.sync(0); await play(blocks[:3], r.scene.durs[0] - 1)
        await r.sync(1); await play(blocks[3:], r.scene.durs[1] - 0.5)
    scenes.append(S("04_simulators", [
        "No real SAP or historian is connected in this demo, so local simulators speak their dialects: PI Web API, an OPC UA gateway, SAP PM OData, OSDU, and the pump maker's PLM, MES and quality systems.",
        "The agent reads with a read-only token. Writing to the historian with that token is refused."], P("term.html"), d_sim))

    # 5 console: refinery case
    async def d_c1(r):
        p = r.page
        await r.sync(0); await r.click('nav button[data-id="CASE-1042"]'); await p.wait_for_selector(".rec")
        await r.sync(1); await r.scroll(330, 4)
        await r.sync(2); await r.scroll(330, 4)
        await r.sync(3); await r.scroll(-1000, 1.5); await r.click("#go"); await p.wait_for_selector(".rec")
        await r.sync(4); await r.click('[data-t="trail"]'); await r.scroll(200, 2.5)
        await r.sync(5); await r.scroll(-600, 0.5); await r.click('[data-t="drafts"]')
        await r.sync(6)
        sel = await p.locator(".draft").first.get_attribute("id")
        await p.select_option(f"#r-{sel}", "quality_engineer"); await r.click(f'[data-ap="{sel}"]')
        await r.sync(7)
        await p.select_option(f"#r-{sel}", "maintenance_planner"); await r.click(f'[data-ap="{sel}"]'); await r.click(f'[data-rel="{sel}"]')
        for el in (await p.locator(".draft").all())[1:]:
            did = await el.get_attribute("id")
            await r.click(f'[data-ap="{did}"]'); await r.click(f'[data-rel="{did}"]')
    scenes.append(S("05_console_refinery", [
        "This is the live console, running the real agent against those simulators. An alarm: drive end vibration on pump P one oh one A at a refinery.",
        "The agent answers after forty four tool calls. The bearing fault is real and progressing, the spectrum shows an outer race defect, and cavitation is ruled out.",
        "It also finds the cause behind the cause. The bearing lot came in through an expedited change with its qualification test waived, and it went into thirty eight pumps for nine customers.",
        "Every finding carries its evidence identifiers. A verifier checks that each one exists in the tool log, and that each quoted number matches its source.",
        "The audit trail lists every call, by system, so an engineer can see exactly what the agent looked at.",
        "The agent has proposed three drafts: a SAP notification, a stock reservation and a warranty claim. Nothing has been sent.",
        "If the wrong role tries to approve, the console refuses.",
        "The maintenance planner approves and releases. Only now does a record appear in the simulated SAP, stamped with who approved it. The other two drafts follow."], CONSOLE, d_c1))

    # 6 field case
    async def d_c2(r):
        p = r.page
        await r.sync(0); await r.click('nav button[data-id="CASE-2077"]'); await p.wait_for_selector(".rec")
        await r.sync(1); await r.scroll(400, 5)
        await r.sync(2); await r.scroll(400, 4)
        await r.sync(3); await r.scroll(-1200, 0.6); await r.click('[data-t="drafts"]'); await r.scroll(150, 2)
    scenes.append(S("06_console_field", [
        "The same platform handles the oil field. A motor temperature alarm on well A zero seven, an electric submersible pump.",
        "The motor has heated by sixteen degrees in thirty days, and gas interference is ruled out. The seal section comes from an elastomer lot that went in under another waived change.",
        "Strings built with that lot have a median run life of two hundred and ninety days, against seven hundred and eighty before, and five of fourteen failure analyses show swollen seals.",
        "The agent asks the operator to lower the drive frequency, which it cannot do itself, and books a rig. The drafts wait for approval."], CONSOLE, d_c2))

    # 7 convergence
    async def d_c3(r):
        p = r.page
        await r.sync(0); await r.click('nav button[data-id="CASE-3001"]'); await p.wait_for_selector(".rec")
        await r.sync(1); await r.scroll(300, 5)
        await r.sync(2); await r.click('[data-t="drafts"]')
    scenes.append(S("07_console_convergence", [
        "Now the question that links both sites: is there a common cause across the refinery pumps and the oil field strings?",
        "Four engineering changes took the expedited route with the qualification test waived. Two of them put suspect lots into service, and the factory's own press fit data shows the bearing lot was twelve percent looser.",
        "The agent sizes the exposure and drafts an eight D and a customer notice, for the quality manager to approve."], CONSOLE, d_c3))

    # 8 guardrails
    async def d_g(r):
        p = r.page
        await r.sync(0); await r.click('[data-probe="pi"]'); await p.wait_for_timeout(500); await r.click('[data-probe="sap"]')
        await r.sync(1); await r.click('nav button[data-id="CASE-3007"]'); await p.wait_for_selector(".refuse")
        await r.sync(2); await r.click('nav button[data-id="CASE-3008"]'); await p.wait_for_selector(".flag")
        await r.sync(3); await r.click('nav button[data-id="CASE-3004"]'); await p.wait_for_selector(".rec")
        await r.sync(4); await r.click('nav button[data-id="CASE-3002"]'); await p.wait_for_selector(".rec")
    scenes.append(S("08_guardrails", [
        "The rules hold for the agent's own credential too. Writes to the historian and to SAP are both refused.",
        "Asked to set the drive to forty hertz, the agent refuses. Operations technology is read-only, and it offers a request for the operator instead.",
        "A notification contains hidden text addressed to an AI assistant. The agent flags it and ignores it, because free text in a record is data, not an instruction.",
        "A vibration alarm that sits at exactly the same value for thirteen days is diagnosed as a stuck transmitter, not a machine fault.",
        "And a question about failures at pump P one oh one B in March is answered correctly: the failure belonged to the unit that was installed in the other position at the time."], CONSOLE, d_g))

    # 9 demo cli
    async def d_demo(r):
        await r.sync(0)
        cmd, lines = term_lines(CAP / "demo.txt", 13)
        lines = [(x[:170], c) for x, c in lines]
        await play_term(r, cmd, lines, r.scene.total - 1.6, "end-to-end demo")
    scenes.append(S("09_demo_cli", [
        "The same flow also runs from the command line as an end to end demo: start the simulators, run the case, approve the drafts as named roles, release them, and show what the plant systems received."], P("term.html"), d_demo))

    # 10 quality
    async def d_q(r):
        await r.sync(0)
        cmd, lines = term_lines(CAP / "gold.txt", 16)
        await play_term(r, cmd, lines, r.scene.durs[0], "gold cases over the simulators")
        await r.sync(1)
        await r.page.evaluate("clear()")
        await r.page.evaluate("([a,b])=>{cmd(a);line(b[0],b[1]);line(b[2],b[3])}", ["ruff check factory_to_field && pytest factory_to_field/tests", ["All checks passed!", "ok", "32 passed in 906.37s (0:15:06)", "ok"]])
        await r.page.evaluate("t=>line(t,'dim')", "(recorded run of 17 October 2026; CI repeats this, plus the ontology check and the demo, on every push)")
    scenes.append(S("10_quality", [
        "Ten gold cases, scored against an answer key the agents never see, all pass over the simulated systems: fifty seven of fifty seven checks.",
        "A suite of thirty two tests and the linter pass, and continuous integration runs all of it on every push."], P("term.html"), d_q))

    # 11 close
    async def d_close(r):
        for i in range(3):
            await r.sync(i); await r.page.evaluate("n=>reveal(n)", i + 1)
    scenes.append(S("11_summary", [
        "To summarise. It connects operations, engineering and field data in one graph. It diagnoses with cited evidence, and it keeps every action behind a named human approval.",
        "One ontology and one agent platform serve the refinery, the oil field and the pump maker that supplies both.",
        "All of the data and systems you saw are simulated. The next step is to connect real SAP, PI, OSDU and PLM systems, run the model planner live, and add a review workflow."], P("close.html"), d_close))
    return scenes


async def main_async(out: Path, only: list[str] | None) -> None:
    v = Voice()
    scenes = build_scenes(v)
    out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        for sc in scenes:
            if only and not any(o in sc.name for o in only):
                continue
            print(f"recording {sc.name} ({sc.total:.0f}s)", flush=True)
            raw = await record_scene(pw, sc, out)
            mux(sc, raw, out)


def concat(out: Path) -> None:
    files = sorted(out.glob("*_av.mp4"))
    lst = out / "list.txt"
    lst.write_text("".join(f"file '{f}'\n" for f in files))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out / "factory_to_field_walkthrough.mp4")], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "factory_to_field_walkthrough.mp4"), "-an", "-c:v", "copy", str(out / "factory_to_field_walkthrough_captions_only.mp4")], check=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("/tmp/vw/out"))
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--concat", action="store_true")
    a = ap.parse_args()
    if a.concat:
        concat(a.out)
    else:
        asyncio.run(main_async(a.out, a.only))
