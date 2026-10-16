"""Entry point: farmer Telegram → NoSQL → aggregation → recommendation → reply."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Allow `python main.py` from project root.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.telegram_bot.bot import FarmerPipelineBot


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    FarmerPipelineBot().run()


if __name__ == "__main__":
    main()
