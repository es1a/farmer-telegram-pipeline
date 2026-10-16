# Farmer Telegram Pipeline

Hackathon MVP of the farmer assistant pipeline. **Telegram** replaces the voice assistant: the farmer writes a message in Telegram (mobile or web), and the backend runs the full flow.

```
Farmer (Telegram)
   │  states problem
   ▼
Telegram interface
   │  persist structured message
   ▼
NoSQL (TinyDB)
   │
   ├──────────────┐
   ▼              ▼
Aggregation  + Weather API + Sensors
   │
   ├──────────────► Dashboard / Excel
   ▼
Recommendation service
   ├─► answer back to Farmer
   └─► notify Officer (optional)
```

## Quick start

1. Create a bot with [@BotFather](https://t.me/BotFather) → copy the token.
2. Configure env:

```bash
cp .env.example .env
# set TELEGRAM_BOT_TOKEN=...
```

3. Install & run:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

4. Open [Telegram Web](https://web.telegram.org) or the app, find your bot, send `/start`, then write a problem like:

> Leaves have yellow spots and the soil looks dry.

You should get a structured reply using weather + mock sensor context.

## Officer notifications

1. Message the bot once and note your `chat id` from `/start`.
2. Put that id in `.env` as `OFFICER_CHAT_ID=...`.
3. Medium/high urgency farmer messages will ping that chat.

## Data outputs

| Path | Purpose |
|------|---------|
| `data/pipeline.json` | NoSQL store (messages + events) |
| `data/dashboard.xlsx` | Aggregation export for demos |

## Project layout

```
main.py
src/
  telegram_bot/     # farmer write / receive answer
  persistence/      # NoSQL
  aggregation/      # weather + sensors + message context
  recommendation/   # answer + officer notify
  dashboard/        # Excel export
```

Weather uses OpenWeatherMap when `OPENWEATHER_API_KEY` is set; otherwise mock weather is used so the pipeline still runs offline.
