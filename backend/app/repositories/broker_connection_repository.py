from uuid import UUID

from sqlalchemy.orm import Session

from app.models.broker_connection import BrokerConnection


class BrokerConnectionRepository:
    """Every method takes user_id and filters by it — this is the concrete
    enforcement of the multi-tenancy rule 'never trust an id supplied by
    the frontend without checking ownership'. There is no method here that
    fetches a BrokerConnection by id alone."""

    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user_id: UUID) -> list[BrokerConnection]:
        return self.db.query(BrokerConnection).filter(BrokerConnection.user_id == user_id).all()

    def get_for_user(self, user_id: UUID, broker: str) -> BrokerConnection | None:
        return (
            self.db.query(BrokerConnection)
            .filter(BrokerConnection.user_id == user_id, BrokerConnection.broker == broker)
            .first()
        )

    def upsert(
        self,
        *,
        user_id: UUID,
        broker: str,
        api_key_encrypted: str,
        api_secret_encrypted: str,
        redirect_uri: str,
    ) -> BrokerConnection:
        conn = self.get_for_user(user_id, broker)
        if conn is None:
            conn = BrokerConnection(user_id=user_id, broker=broker)
        conn.api_key_encrypted = api_key_encrypted
        conn.api_secret_encrypted = api_secret_encrypted
        conn.redirect_uri = redirect_uri
        # Changing credentials invalidates any existing session with the broker.
        conn.access_token_encrypted = None
        conn.access_token_expires_at = None
        conn.analytics_token_encrypted = None
        conn.analytics_token_expires_at = None
        conn.is_connected = False
        conn.last_error = None
        self.db.add(conn)
        self.db.commit()
        self.db.refresh(conn)
        return conn

    def save(self, conn: BrokerConnection) -> BrokerConnection:
        self.db.add(conn)
        self.db.commit()
        self.db.refresh(conn)
        return conn

    def delete(self, conn: BrokerConnection) -> None:
        self.db.delete(conn)
        self.db.commit()
