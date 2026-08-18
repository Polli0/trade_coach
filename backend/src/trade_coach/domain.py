from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from enum import StrEnum


class TradeSide(StrEnum):
    BUY = "buy"
    SELL = "sell"

class RiskEvaluation(StrEnum):
    EXCEEDED = "exceeded"
    WITHIN_LIMIT = "within_limit"
    UNKNOWN = "unknown"

class CoachMessageKind(StrEnum):
    RISK_LIMIT_EXCEEDED = "risk_limit_exceeded"
    RISK_UNKNOWN = "risk_unknown"
    TRADE_AFTER_STOP_LOSSES = "trade_after_stop_losses"

class TradeOutcome(StrEnum):
    PROFIT = "profit"
    LOSS = "loss"
    BREAK_EVEN = "break_even"

class CloseReason(StrEnum):
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    MANUAL = "manual"
    OTHER = "other"

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
    max_daily_stop_losses: int = 2

    def __post_init__(self) -> None:
        if self.max_risk_percentage <= Decimal("0"):
            raise ValueError("max risk percentage must be greater than zero")
        if self.max_daily_stop_losses <= 0:
            raise ValueError("max daily stop loss must be greater than zero")

    def evaluate_risk(self, position: PositionOpened) -> RiskEvaluation:
        if self.account_id != position.account_id:
            raise ValueError("position and trading plan must belong to the same account")
        risk_percentage = position.risk_percentage
        if risk_percentage is None:
            return RiskEvaluation.UNKNOWN
        else:
            if risk_percentage > self.max_risk_percentage:
                return RiskEvaluation.EXCEEDED
            return RiskEvaluation.WITHIN_LIMIT

@dataclass(frozen=True, slots=True)
class CoachMessage:
    account_id: str
    position_id: str | None
    occurred_at: datetime
    kind: CoachMessageKind
    title: str
    body: str

@dataclass(frozen=True, slots=True)
class PositionClosed:
    event_id: str
    account_id: str
    position_id: str
    occurred_at: datetime
    symbol: str
    side: TradeSide
    profit: Decimal
    commission: Decimal
    close_price: Decimal
    swap: Decimal
    fee: Decimal
    close_reason: CloseReason

    @property
    def net_profit(self) -> Decimal:
        return self.profit + self.commission + self.swap + self.fee

    @property
    def outcome(self) -> TradeOutcome:
        if self.net_profit > 0:
            return TradeOutcome.PROFIT

        if self.net_profit < 0:
            return TradeOutcome.LOSS

        return TradeOutcome.BREAK_EVEN

@dataclass(frozen=True, slots=True)
class DailySummary:
    account_id: str
    day: date
    closed_positions: tuple[PositionClosed, ...]

    def __post_init__(self) -> None:
        for position in self.closed_positions:
            if position.account_id != self.account_id:
                raise ValueError(
                    "closed position and daily summary must belong to the same account"
                )

            if position.occurred_at.date() != self.day:
                raise ValueError(
                    "closed position and daily summary must belong to the same day"
                )

    @property
    def stop_loss_count(self) -> int:
        result = 0

        for x in self.closed_positions:
            if x.close_reason is CloseReason.STOP_LOSS:
                result += 1

        return result

    @property
    def net_profit(self) -> Decimal:
        result = Decimal("0")

        for x in self.closed_positions:
            result += x.net_profit

        return result
