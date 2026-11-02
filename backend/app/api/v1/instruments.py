from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin
from app.models.user import User
from app.repositories.instrument_repository import InstrumentRepository
from app.schemas.instrument import InstrumentOut
from app.schemas.market_universe import Nifty500UniverseImport, MarketUniverseSnapshotOut
from app.services.instrument_service import InstrumentService
from app.services.market_universe_service import MarketUniverseImportError, MarketUniverseService

router = APIRouter(prefix="/instruments", tags=["instruments"])


@router.get("/search", response_model=list[InstrumentOut])
def search_instruments(q: str = Query(min_length=1, max_length=50), db: Session = Depends(get_db)):
    return InstrumentRepository(db).search(q)


@router.post("/seed", response_model=dict)
def seed_default_instruments(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    count = InstrumentService(db).seed_defaults()
    return {"seeded": count}


@router.post("/sync", response_model=dict)
async def sync_instruments_from_upstox(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    ok, message = await InstrumentService(db).sync_from_upstox()
    return {"success": ok, "message": message}



@router.post("/universe/nifty-500/snapshots", response_model=MarketUniverseSnapshotOut)
def import_nifty500_universe(
    payload: Nifty500UniverseImport,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Import a dated, complete Nifty 500 constituent list from an official source."""
    try:
        snapshot = MarketUniverseService(db).import_nifty500(
            symbols=payload.symbols,
            as_of_date=payload.as_of_date,
            source=payload.source,
        )
    except MarketUniverseImportError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return MarketUniverseSnapshotOut(
        snapshot_id=str(snapshot.id),
        universe_key=snapshot.universe_key,
        as_of_date=snapshot.as_of_date,
        source=snapshot.source,
        member_count=snapshot.member_count,
    )
