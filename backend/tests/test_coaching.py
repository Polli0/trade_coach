import unittest
from datetime import UTC, datetime
from decimal import Decimal

from trade_coach.coaching import create_risk_message
from trade_coach.domain import CoachMessageKind, PositionOpened, TradeSide, TradingPlan

def make_position_opened(
    *,
    equity: Decimal = Decimal("10000"),
    risk_amount: Decimal | None = Decimal("100"),
    stop_loss: Decimal | None = Decimal("1.14500"),
    volume: Decimal = Decimal("0.10"),
) -> PositionOpened:
    return PositionOpened(
        event_id="event-1",
        account_id="account-1",
        position_id="position-1",
        occurred_at=datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
        symbol="EURUSD",
        side=TradeSide.BUY,
        volume=volume,
        entry_price=Decimal("1.15000"),
        stop_loss=stop_loss,
        take_profit=Decimal("1.16000"),
        equity=equity,
        risk_amount=risk_amount,
    )

class RiskMessageTests(unittest.TestCase):
    def test_creates_message_when_risk_limit_is_exceeded(self) -> None:
        position = make_position_opened(
            equity = Decimal("10000"),
            risk_amount = Decimal("200"),
        )

        plan = TradingPlan(
            account_id = "account-1",
            max_risk_percentage = Decimal("1")
        )

        message = create_risk_message(position, plan)

        self.assertIsNotNone(message)
        self.assertEqual(message.kind, CoachMessageKind.RISK_LIMIT_EXCEEDED)
        self.assertEqual(message.account_id, position.account_id)
        self.assertEqual(message.position_id, position.position_id)
        self.assertEqual(message.occurred_at, position.occurred_at)

    def test_when_limit_is_within_limit(self) -> None:
        position = make_position_opened(
            risk_amount= Decimal("100"),
        )

        plan = TradingPlan(
            account_id = "account-1",
            max_risk_percentage = Decimal("1"),
        )

        message = create_risk_message(position, plan)

        self.assertIsNone(message)

    def test_when_limit_is_unknown(self) -> None:
        position = make_position_opened(
            risk_amount= None,
            stop_loss= None,
        )

        plan = TradingPlan(
            account_id = "account-1",
            max_risk_percentage = Decimal("1"),
        )

        message = create_risk_message(position, plan)

        self.assertIsNotNone(message)
        self.assertIsInstance(message.body, str)
        self.assertEqual(message.kind, CoachMessageKind.RISK_UNKNOWN)