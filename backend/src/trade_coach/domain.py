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
        return (self.risk_amount / self.equity) * Decimal("100")

@dataclass
class TradingPlan:
    account_id: str
    max_risk_percentage: Decimal #The risk it will decide from the user.

    def __post_init__(self) -> None:
        if self.max_risk_percentage <= Decimal("0"):
            raise ValueError("max risk percentage must be greater than zero")

    def is_risk_exceeded_by(self, position: PositionOpened) -> bool | None:
        if self.account_id == position.account_id:
            risk_percentage = position.risk_percentage
            if risk_percentage is None:
                return None
            return risk_percentage > self.max_risk_percentage