#!/usr/bin/env python3
"""Live-check the official Upstox BOD file and sync it only to throwaway SQLite.

This deliberately never reads or writes the configured application database.
It verifies real upstream availability, parsing, segment coverage and the same
snapshot reconciliation path used by the application.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session

from app.core.database import Base
import app.models  # noqa: F401 - register every ORM model
from app.models.instrument import Instrument
from app.services.instrument_service import (
    MIN_VALID_SNAPSHOT_RECORDS,
    InstrumentService,
    _REQUIRED_SNAPSHOT_SEGMENTS,
)


async def main() -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        ok, message = await InstrumentService(db).sync_from_upstox()
        if not ok:
            print(json.dumps({"ok": False, "message": message}, indent=2))
            return 1

        total = db.query(Instrument).filter(Instrument.is_active.is_(True)).count()
        by_segment = dict(
            db.query(Instrument.segment, func.count(Instrument.id))
            .filter(Instrument.is_active.is_(True))
            .group_by(Instrument.segment)
            .all()
        )
        missing = sorted(_REQUIRED_SNAPSHOT_SEGMENTS - set(by_segment))
        if total < MIN_VALID_SNAPSHOT_RECORDS or missing:
            print(json.dumps({
                "ok": False,
                "message": "Live master synced but post-sync completeness checks failed.",
                "active_instruments": total,
                "missing_required_segments": missing,
                "segments": by_segment,
            }, indent=2))
            return 1

        print(json.dumps({
            "ok": True,
            "source": "official Upstox complete.json.gz",
            "database": "throwaway in-memory SQLite (not application database)",
            "active_instruments": total,
            "segments": dict(sorted(by_segment.items())),
            "required_segments_present": True,
            "result": message,
        }, indent=2))
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
