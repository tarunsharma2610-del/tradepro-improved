from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_admin
from app.middleware.audit import write_audit_log
from app.models.user import User
from app.schemas.broker import (
    BrokerAuthorizeUrl,
    BrokerConnectionCreate,
    BrokerConnectionOut,
    BrokerConnectionTestResult,
)
from app.schemas.platform_setting import PlatformSettingOut, PlatformSettingUpdate
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.platform_settings_service import PlatformSettingsService
from app.services.telegram_service import TelegramService, TelegramServiceError

router = APIRouter(prefix="/settings", tags=["settings"])


# ---------- Per-user broker credentials ----------


@router.get("/broker", response_model=list[BrokerConnectionOut])
def list_broker_connections(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = BrokerCredentialsService(db)
    return [service.to_masked_out(c) for c in service.list_connections(user.id)]


@router.put("/broker", response_model=BrokerConnectionOut)
def save_broker_connection(
    payload: BrokerConnectionCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = BrokerCredentialsService(db)
    conn = service.save_credentials(user.id, payload)
    write_audit_log(
        db, action="broker_connection.saved", user_id=user.id, request=request,
        resource_type="broker_connection", resource_id=str(conn.id), metadata={"broker": payload.broker},
    )
    return service.to_masked_out(conn)


@router.delete("/broker/{broker}", status_code=status.HTTP_204_NO_CONTENT)
def delete_broker_connection(
    broker: str, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    service = BrokerCredentialsService(db)
    try:
        service.delete_connection(user.id, broker)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    write_audit_log(db, action="broker_connection.deleted", user_id=user.id, request=request, metadata={"broker": broker})


@router.get("/broker/{broker}/authorize-url", response_model=BrokerAuthorizeUrl)
def get_broker_authorize_url(broker: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = BrokerCredentialsService(db)
    try:
        url = service.get_authorize_url(user.id, broker)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return BrokerAuthorizeUrl(authorize_url=url)


class OAuthCallbackBody(BaseModel):
    code: str
    state: str


@router.post("/broker/{broker}/callback", response_model=BrokerConnectionOut)
async def broker_oauth_callback(
    broker: str,
    payload: OAuthCallbackBody,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = BrokerCredentialsService(db)
    try:
        conn = await service.complete_oauth(user.id, broker, payload.code, payload.state)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    write_audit_log(
        db, action="broker_connection.oauth_completed", user_id=user.id, request=request,
        metadata={"broker": broker, "connected": conn.is_connected},
    )
    return service.to_masked_out(conn)


@router.post("/broker/{broker}/test", response_model=BrokerConnectionTestResult)
async def test_broker_connection(broker: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = BrokerCredentialsService(db)
    try:
        ok, message = await service.test_connection(user.id, broker)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return BrokerConnectionTestResult(success=ok, message=message)


# ---------- Admin-only platform integration settings ----------


@router.get("/platform", response_model=list[PlatformSettingOut])
def list_platform_settings(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return PlatformSettingsService(db).list_settings()


@router.put("/platform", response_model=PlatformSettingOut)
def set_platform_setting(
    payload: PlatformSettingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = PlatformSettingsService(db)
    try:
        result = service.set_setting(
            key=payload.key, value=payload.value, description=payload.description, admin_user_id=admin.id
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    write_audit_log(
        db, action="platform_setting.updated", user_id=admin.id, request=request, metadata={"key": payload.key}
    )
    return result


# ---------- Per-user notification channels ----------


class TelegramLinkOut(BaseModel):
    telegram_deep_link: str


class TelegramStatusOut(BaseModel):
    linked: bool
    linked_at: str | None = None


class WhatsAppNumberUpdate(BaseModel):
    whatsapp_number: str | None = None


class WhatsAppNumberOut(BaseModel):
    whatsapp_number: str | None


@router.post("/telegram/link", response_model=TelegramLinkOut)
async def start_telegram_link(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        deep_link = await TelegramService(db).start_link(user.id)
    except TelegramServiceError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return TelegramLinkOut(telegram_deep_link=deep_link)


@router.get("/telegram/status", response_model=TelegramStatusOut)
def telegram_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    from app.repositories.telegram_link_repository import TelegramLinkRepository

    link = TelegramLinkRepository(db).get_for_user(user.id)
    if link is None or link.telegram_chat_id is None:
        return TelegramStatusOut(linked=False)
    return TelegramStatusOut(linked=True, linked_at=link.linked_at.isoformat() if link.linked_at else None)


@router.delete("/telegram/link", status_code=status.HTTP_204_NO_CONTENT)
def unlink_telegram(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    TelegramService(db).unlink(user.id)


@router.get("/whatsapp", response_model=WhatsAppNumberOut)
def get_whatsapp_number(user: User = Depends(get_current_user)):
    return WhatsAppNumberOut(whatsapp_number=user.whatsapp_number)


@router.put("/whatsapp", response_model=WhatsAppNumberOut)
def set_whatsapp_number(payload: WhatsAppNumberUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.whatsapp_number and not payload.whatsapp_number.startswith("+"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Use E.164 format, e.g. +919876543210.")
    user.whatsapp_number = payload.whatsapp_number
    db.add(user)
    db.commit()
    return WhatsAppNumberOut(whatsapp_number=user.whatsapp_number)
