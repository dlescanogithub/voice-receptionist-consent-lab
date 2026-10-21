"""Voice A/B probe over the ElevenLabs Conversational AI WebSocket.

Sends a fixed caller script as text and records every agent turn as 16 kHz PCM WAV,
so the same sentence can be compared at different positions in a call (T1, T2, T3).

THIS SPENDS ELEVENLABS CREDITS. It refuses to run unless LIVE_ENABLED=1.
Nothing is hard-coded: the key and the agent identifiers come from the environment.

    export ELEVENLABS_API_KEY=...       # never commit it
    export ELEVENLABS_AGENT_ID=...      # your own agent
    export ELEVENLABS_BRANCH_ID=...     # optional: a test branch, not main
    LIVE_ENABLED=1 python tools/ws_ab.py evidence/ab/MYRUN

Notes from the runs in evidence/ab/:
- The server ignores `user_message` unless the client also streams audio, so a
  silent `user_audio_chunk` is sent every 100 ms.
- The script waits for real-time playback to finish before sending the next line.
- Measure the result offline with tools/measure_ab.py.
"""
import asyncio, base64, json, os, sys, time, urllib.parse, urllib.request, wave

import websockets

SCRIPT = ["Hola, quiero un turno con clínica médica", "Sí", "El viernes a la mañana"]


def signed_url(key: str, agent: str, branch: str | None) -> str:
    q = {"agent_id": agent}
    if branch:
        q["branch_id"] = branch
    url = "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"xi-api-key": key})
    return json.load(urllib.request.urlopen(req))["signed_url"]


async def run(out: str, key: str, agent: str, branch: str | None) -> None:
    os.makedirs(out, exist_ok=True)
    script = list(SCRIPT)
    async with websockets.connect(signed_url(key, agent, branch), max_size=None) as ws:
        init = {"type": "conversation_initiation_client_data"}
        if branch:
            init["branch_id"] = branch
        await ws.send(json.dumps(init))
        cur, texts, durs = bytearray(), [], []
        state = {"last": None, "first_audio": None, "fmt": None}
        silence = base64.b64encode(b"\0" * 3200).decode()

        async def feed() -> None:
            while True:
                await ws.send(json.dumps({"user_audio_chunk": silence}))
                await asyncio.sleep(0.1)

        feeder = asyncio.create_task(feed())

        async def recv_until_quiet(timeout: float = 20) -> None:
            t0 = time.time()
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
                except asyncio.TimeoutError:
                    if cur and state["last"] and time.time() - state["last"] > 1.0:
                        return
                    if time.time() - t0 > timeout:
                        return
                    continue
                e = json.loads(msg)
                ty = e.get("type")
                if ty == "ping":
                    await ws.send(json.dumps({"type": "pong", "event_id": e["ping_event"]["event_id"]}))
                elif ty == "conversation_initiation_metadata":
                    state["fmt"] = e["conversation_initiation_metadata_event"].get("agent_output_audio_format")
                elif ty == "audio":
                    if not cur:
                        state["first_audio"] = time.time()
                    cur.extend(base64.b64decode(e["audio_event"]["audio_base_64"]))
                    state["last"] = time.time()
                elif ty == "agent_response":
                    texts.append(e["agent_response_event"]["agent_response"])

        for k in range(len(script) + 1):
            await recv_until_quiet()
            dur = len(cur) / 32000
            durs.append(dur)
            with wave.open(f"{out}/T{k + 1}.wav", "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(bytes(cur))
            cur.clear(); state["last"] = None
            if state["first_audio"]:
                await asyncio.sleep(max(0, state["first_audio"] + dur + 0.4 - time.time()))
            if k < len(script):
                await ws.send(json.dumps({"type": "user_message", "text": script[k]}))
        feeder.cancel()
        # conversation ids are deliberately not written to disk
        json.dump({"fmt": state["fmt"], "texts": texts, "durs": durs}, open(f"{out}/meta.json", "w"),
                  ensure_ascii=False, indent=1)
        print(out, [round(d, 2) for d in durs])


def main() -> None:
    if os.environ.get("LIVE_ENABLED") != "1":
        print("refusing: this spends ElevenLabs credits. Set LIVE_ENABLED=1 to run.", file=sys.stderr)
        sys.exit(2)
    key = os.environ.get("ELEVENLABS_API_KEY")
    agent = os.environ.get("ELEVENLABS_AGENT_ID")
    if not key or not agent or len(sys.argv) < 2:
        print("need ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID and an output dir", file=sys.stderr)
        sys.exit(2)
    asyncio.run(run(sys.argv[1], key, agent, os.environ.get("ELEVENLABS_BRANCH_ID")))


if __name__ == "__main__":
    main()
