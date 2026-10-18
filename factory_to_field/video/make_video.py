"""Records the walkthrough video from the real console, real command output and a few explanatory cards.

    python -m factory_to_field.video.make_video --out /tmp/vw/out

Needs: playwright with chromium, ffmpeg, espeakng-loader (pip), the live console running on :8800
(python -m factory_to_field.ui.live_app --port 8800) and the captured command outputs in --cap (see cap.sh in the notes).
Narration is synthetic (espeak-ng); captions are burned in, and a captions-only cut is written as well.
"""
from __future__ import annotations

import argparse
import asyncio
import ctypes
import json
import subprocess
import time
import wave
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
PAGES = HERE / "pages"
W, H = 1600, 900
GAP = 0.45


# ------------------------------------------------------------------ narration
class Voice:
    def __init__(self) -> None:
        from espeakng_loader import get_data_path, get_library_path
        self.lib = ctypes.CDLL(get_library_path())
        self.sr = self.lib.espeak_Initialize(2, 0, get_data_path().encode(), 0)
        self.buf: list[bytes] = []
        cb_t = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)

        def cb(w, n, ev):
            if w:
                self.buf.append(ctypes.string_at(w, n * 2))
            return 0
        self._cb = cb_t(cb)
        self.lib.espeak_SetSynthCallback(self._cb)
        self.lib.espeak_SetVoiceByName(b"en-us")
        self.lib.espeak_SetParameter(1, 158, 0)   # rate
        self.lib.espeak_SetParameter(3, 55, 0)    # pitch

    def say(self, text: str) -> bytes:
        self.buf.clear()
        t = text.encode()
        self.lib.espeak_Synth(t, len(t) + 1, 0, 0, 0, 1, None, None)
        self.lib.espeak_Synchronize()
        return b"".join(self.buf)


def write_wav(path: Path, pcm: bytes, sr: int) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm)


# ------------------------------------------------------------------ browser helpers
CURSOR_JS = """
document.addEventListener('mousemove',e=>{const c=document.getElementById('cur');if(c){c.style.left=e.clientX+'px';c.style.top=e.clientY+'px'}});
document.addEventListener('mousedown',()=>{const c=document.getElementById('cur');c&&c.classList.add('dn')});
document.addEventListener('mouseup',()=>{const c=document.getElementById('cur');c&&c.classList.remove('dn')});
window.setCap=t=>{const c=document.getElementById('cap');if(!c)return;if(!t){c.classList.remove('on');return}c.textContent=t;c.classList.add('on')};
"""
CAP_HTML = """
if(!document.getElementById('cap')){const c=document.createElement('div');c.id='cap';document.body.appendChild(c)}
if(!document.getElementById('cur')){const c=document.createElement('div');c.id='cur';document.body.appendChild(c)}
const st=document.createElement('style');st.textContent=`%CSS%`;document.head.appendChild(st);
"""


class Scene:
    def __init__(self, name: str, sentences: list[str], page_url: str, driver, voice_pcm: list[bytes], sr: int, css_extra: bool = False) -> None:
        self.name, self.sentences, self.url, self.driver, self.pcm, self.sr = name, sentences, page_url, driver, voice_pcm, sr
        self.durs = [len(p) / 2 / sr for p in voice_pcm]
        self.starts, t = [], 0.0
        for d in self.durs:
            self.starts.append(t); t += d + GAP
        self.total = t + 0.4


class Run:
    def __init__(self, page, scene: Scene) -> None:
        self.page, self.scene, self.t0 = page, scene, time.time()

    def now(self) -> float:
        return time.time() - self.t0

    async def sync(self, i: int) -> None:
        d = self.scene.starts[i] - self.now()
        if d > 0:
            await self.page.wait_for_timeout(int(d * 1000))
        await self.page.evaluate("t=>window.setCap(t)", self.scene.sentences[i])

    async def until(self, t: float) -> None:
        d = t - self.now()
        if d > 0:
            await self.page.wait_for_timeout(int(d * 1000))

    async def move(self, sel: str, steps: int = 14) -> None:
        box = await self.page.locator(sel).first.bounding_box()
        await self.page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=steps)

    async def click(self, sel: str) -> None:
        await self.page.locator(sel).first.scroll_into_view_if_needed()
        await self.move(sel)
        await self.page.wait_for_timeout(150)
        await self.page.mouse.down(); await self.page.wait_for_timeout(70); await self.page.mouse.up()
        await self.page.wait_for_timeout(150)

    async def scroll(self, dy: int, secs: float, sel: str | None = None) -> None:
        n = max(1, int(secs * 20))
        for _ in range(n):
            await self.page.evaluate("([dy,sel])=>(sel?document.querySelector(sel):window).scrollBy(0,dy)", [dy / n, sel])
            await self.page.wait_for_timeout(50)


async def record_scene(pw, scene: Scene, out: Path) -> Path:
    b = await pw.chromium.launch()
    vid = out / f"{scene.name}_raw"
    vid.mkdir(parents=True, exist_ok=True)
    t_ctx = time.time()
    ctx = await b.new_context(viewport={"width": W, "height": H}, record_video_dir=str(vid), record_video_size={"width": W, "height": H})
    page = await ctx.new_page()
    await page.goto(scene.url)
    await page.wait_for_load_state("networkidle")
    css = (PAGES / "common.css").read_text().replace("`", "")
    await page.evaluate(CAP_HTML.replace("%CSS%", css))
    await page.evaluate(CURSOR_JS)
    await page.mouse.move(W - 60, H - 160)
    lead = time.time() - t_ctx
    r = Run(page, scene)
    await scene.driver(r)
    await r.until(scene.total)
    await page.evaluate("window.setCap('')")
    await ctx.close(); await b.close()
    webm = next(vid.glob("*.webm"))
    mp4 = out / f"{scene.name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{lead:.2f}", "-i", str(webm), "-vf", f"scale=1920:1080:flags=lanczos,fps=30,format=yuv420p",
                    "-an", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", str(mp4)], check=True)
    return mp4


def mux(scene: Scene, video: Path, out: Path) -> Path:
    pcm = b""
    for p in scene.pcm:
        pcm += p + b"\0\0" * int(scene.sr * GAP)
    pcm += b"\0\0" * int(scene.sr * 0.4)
    wav = out / f"{scene.name}.wav"
    write_wav(wav, pcm, scene.sr)
    res = out / f"{scene.name}_av.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(wav), "-filter_complex", "[0:v]tpad=stop_mode=clone:stop_duration=5[v]", "-map", "[v]", "-map", "1:a",
                    "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "1", "-t", f"{scene.total:.2f}", str(res)], check=True)
    return res
