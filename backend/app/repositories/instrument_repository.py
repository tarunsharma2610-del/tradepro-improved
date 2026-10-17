from uuid import UUID

from sqlalchemy.orm import Session

from app.models.instrument import Instrument


class InstrumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, instrument_id: UUID) -> Instrument | None:
        return self.db.get(Instrument, instrument_id)

    def get_by_key(self, instrument_key: str) -> Instrument | None:
        return self.db.query(Instrument).filter(Instrument.instrument_key == instrument_key).first()

    def search(self, query: str, limit: int = 20) -> list[Instrument]:
        like = f"%{query.upper()}%"
        return (
            self.db.query(Instrument)
            .filter(Instrument.is_active.is_(True))
            .filter(
                (Instrument.trading_symbol.ilike(like)) | (Instrument.name.ilike(like))
            )
            .order_by(Instrument.trading_symbol)
            .limit(limit)
            .all()
        )

    def upsert(self, **fields) -> Instrument:
        existing = self.get_by_key(fields["instrument_key"])
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            instrument = existing
        else:
            instrument = Instrument(**fields)
        self.db.add(instrument)
        self.db.commit()
        self.db.refresh(instrument)
        return instrument

    def count(self) -> int:
        return self.db.query(Instrument).count()
