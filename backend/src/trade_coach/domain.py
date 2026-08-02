from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class TradeSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True, slots=True)
class PositionOpened:
    event_id: str
    account_id: str
    position_id: str
    occurred_at: datetime
    symbol: str
    side: TradeSide
    volume: Decimal
    entry_price: Decimal
    stop_loss: Decimal | None
    take_profit: Decimal | None
    equity: Decimal
    risk_amount: Decimal | None

    def __post_init__(self) -> None:
        if self.equity <= Decimal("0"):
            raise ValueError("equity must be greater than zero")

        if self.volume <= Decimal("0"):
            raise ValueError("volume must be greater than zero")


    @property
    def risk_percentage(self) -> Decimal | None:
        if self.risk_amount is None:
            return None
        else:
            return (self.risk_amount / self.equity) * Decimal("100")