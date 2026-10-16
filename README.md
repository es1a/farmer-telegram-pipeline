# Farmer Telegram Pipeline

Farmers state a problem via Telegram. Teammates consume the same events over HTTP or WebSocket.

## Run (one process: bot + API)

```bash
cp .env.example .env   # set TELEGRAM_BOT_TOKEN from @BotFather
pip install -r requirements.txt
python main.py
```

Only **one** `python main.py` at a time (Telegram allows a single polling client).

Then open Telegram, message the bot, and send **text or a voice note**. Voice notes are transcribed with OpenAI Whisper (set `OPENAI_API_KEY` in `.env`). Each problem is appended to `problems.jsonl` and pushed to WebSocket clients.

## API for teammates

Default: `http://<host>:8000` (override with `API_HOST` / `API_PORT` in `.env`).

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness |
| `GET /problems` | Full history (JSON array) |
| `WS /ws/problems` | Live stream — one JSON object per new problem |

### Example (history)

```bash
curl http://127.0.0.1:8000/problems
```

### Example (live WebSocket)

```js
const ws = new WebSocket("ws://127.0.0.1:8000/ws/problems");
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

### Event shape

```json
{
  "user_id": 6389067622,
  "username": null,
  "first_name": "Esra",
  "chat_id": 6389067622,
  "problem": "…",
  "source": "text",
  "received_at": "2026-10-16T19:15:09+00:00"
}
```

`source` is `"text"` or `"voice"` (voice = Whisper transcript; audio is not stored).

On the same Wi‑Fi, share `http://<your-lan-ip>:8000`. For remote teammates, tunnel or deploy and use `wss://`.
