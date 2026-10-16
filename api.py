"""HTTP + WebSocket API for teammates to consume farmer problems."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

PROBLEMS_PATH = Path(__file__).resolve().parent / "problems.jsonl"

logger = logging.getLogger(__name__)


class ProblemHub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)
        logger.info("WebSocket client connected (%s total)", len(self._clients))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(websocket)
        logger.info("WebSocket client disconnected (%s total)", len(self._clients))

    async def broadcast(self, record: dict) -> None:
        payload = json.dumps(record, ensure_ascii=False)
        async with self._lock:
            clients = list(self._clients)
        dead: list[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)


hub = ProblemHub()


def load_problems() -> list[dict]:
    if not PROBLEMS_PATH.exists():
        return []
    records: list[dict] = []
    with PROBLEMS_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def append_problem(record: dict) -> None:
    with PROBLEMS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


async def publish_problem(record: dict) -> None:
    append_problem(record)
    await hub.broadcast(record)


def create_app() -> FastAPI:
    app = FastAPI(title="Farmer Problem API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True}

    @app.get("/problems")
    async def list_problems() -> list[dict]:
        return load_problems()

    @app.websocket("/ws/problems")
    async def problems_ws(websocket: WebSocket) -> None:
        await hub.connect(websocket)
        try:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
        except WebSocketDisconnect:
            pass
        finally:
            await hub.disconnect(websocket)

    return app


app = create_app()
