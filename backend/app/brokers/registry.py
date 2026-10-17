from app.brokers.base import BrokerAdapter
from app.brokers.upstox.adapter import UpstoxAdapter

_ADAPTERS: dict[str, BrokerAdapter] = {
    "upstox": UpstoxAdapter(),
}


def get_broker_adapter(broker: str) -> BrokerAdapter:
    try:
        return _ADAPTERS[broker]
    except KeyError:
        raise ValueError(f"Unknown broker '{broker}'. Supported: {list(_ADAPTERS)}")


def supported_brokers() -> list[str]:
    return list(_ADAPTERS)
