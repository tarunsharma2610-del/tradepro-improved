from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin
from app.models.user import User
from app.repositories.instrument_repository import InstrumentRepository
from app.schemas.instrument import InstrumentOut
from app.services.instrument_service import InstrumentService

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
