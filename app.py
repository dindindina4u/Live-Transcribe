"""
Live Captions relay
--------------------
A tiny server that does two jobs:

1. Serves the phone web app (index.html + manifest).
2. Bridges the phone's microphone audio to Sarvam's streaming
   speech-to-text WebSocket, holding your API key safely on the
   server (so it never lives on your phone or in the web page).

Run locally:
    pip install -r requirements.txt
    export SARVAM_API_KEY="your_key_here"     # Windows: set SARVAM_API_KEY=...
    python app.py

It listens on PORT (default 8080). On a host like Render, PORT is set for you.
"""

import os
import asyncio
from urllib.parse import urlencode

from aiohttp import web, ClientSession, WSMsgType

SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "").strip()
SARVAM_WS = "wss://api.sarvam.ai/speech-to-text/ws"
PORT = int(os.environ.get("PORT", "8080"))

HERE = os.path.dirname(os.path.abspath(__file__))


async def index(_request):
    return web.FileResponse(os.path.join(HERE, "index.html"))


async def manifest(_request):
    return web.FileResponse(os.path.join(HERE, "manifest.webmanifest"))


def build_upstream_url(lang: str, mode: str) -> str:
    # 'translate' auto-detects the language, so we send 'unknown' for it.
    if mode == "translate":
        lang = "unknown"
    params = {
        "model": "saaras:v3",
        "mode": mode if mode in ("transcribe", "translate") else "transcribe",
        "language-code": lang or "te-IN",
        "sample_rate": "16000",
        "input_audio_codec": "pcm_s16le",   # we stream raw 16-bit PCM
        "high_vad_sensitivity": "true",      # snappier turn-taking for live use
        "vad_signals": "false",
    }
    return f"{SARVAM_WS}?{urlencode(params)}"


async def stt(request):
    """One phone connection <-> one Sarvam connection."""
    client_ws = web.WebSocketResponse(max_msg_size=0)
    await client_ws.prepare(request)

    if not SARVAM_API_KEY:
        await client_ws.send_json({"type": "error", "message": "Server missing SARVAM_API_KEY"})
        await client_ws.close()
        return client_ws

    lang = request.query.get("lang", "te-IN")
    mode = request.query.get("mode", "transcribe")
    url = build_upstream_url(lang, mode)

    session = ClientSession()
    try:
        upstream = await session.ws_connect(
            url, headers={"Api-Subscription-Key": SARVAM_API_KEY}, max_msg_size=0, heartbeat=20
        )
    except Exception:
        await client_ws.send_json(
            {"type": "error", "message": "Could not reach Sarvam — check the API key and credits."}
        )
        await client_ws.close()
        await session.close()
        return client_ws

    async def phone_to_sarvam():
        async for msg in client_ws:
            if msg.type == WSMsgType.TEXT:
                await upstream.send_str(msg.data)
            elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSING, WSMsgType.ERROR):
                break

    async def sarvam_to_phone():
        async for msg in upstream:
            if msg.type == WSMsgType.TEXT:
                await client_ws.send_str(msg.data)
            elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSING, WSMsgType.ERROR):
                break

    t1 = asyncio.create_task(phone_to_sarvam())
    t2 = asyncio.create_task(sarvam_to_phone())
    try:
        done, pending = await asyncio.wait({t1, t2}, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
    finally:
        await upstream.close()
        await session.close()
        if not client_ws.closed:
            await client_ws.close()
    return client_ws


def make_app():
    app = web.Application()
    app.add_routes([
        web.get("/", index),
        web.get("/manifest.webmanifest", manifest),
        web.get("/stt", stt),
    ])
    return app


if __name__ == "__main__":
    if not SARVAM_API_KEY:
        print("WARNING: SARVAM_API_KEY is not set. The captions will not work until you set it.")
    web.run_app(make_app(), host="0.0.0.0", port=PORT)
