from sqlalchemy import UniqueConstraint

from app.models.order import Order


def test_paper_stop_event_order_reference_is_nullable_and_unique():
    column = Order.__table__.c.paper_stop_event_id
    assert column.nullable is True
    assert any(
        isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_orders_paper_stop_event"
        and [item.name for item in constraint.columns] == ["paper_stop_event_id"]
        for constraint in Order.__table__.constraints
    )
    assert any(
        foreign_key.target_fullname == "paper_stop_events.id"
        and foreign_key.ondelete == "RESTRICT"
        for foreign_key in column.foreign_keys
    )
