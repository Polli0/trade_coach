import unittest
from datetime import UTC, datetime
from decimal import Decimal

from trade_coach.domain import TradeSide, PositionOpened

class PositionOpenedTests(unittest.TestCase):
    def test_calculates_risk_percentage(self) -> None:
        event = PositionOpened(
            event_id = "event-1",
            account_id="account-1",
            position_id="position-1",
            occurred_at=datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=Decimal("0.10"),
            entry_price=Decimal("1.15000"),
            stop_loss=Decimal("1.14500"),
            take_profit=Decimal("1.16000"),
            equity=Decimal("10000"),
            risk_amount=Decimal("100"),
        )

        self.assertEqual(event.risk_percentage, Decimal("1"))

    def test_returns_none_when_risk_amount_is_missing(self) -> None:
        event = PositionOpened(
            event_id="event-2",
            account_id="account-1",
            position_id="position-2",
            occurred_at=datetime(2026, 8, 2, 9, 0, tzinfo=UTC),
            symbol="EURUSD",
            side=TradeSide.BUY,
            volume=Decimal("0.10"),
            entry_price=Decimal("1.15000"),
            stop_loss=None,
            take_profit=Decimal("1.16000"),
            equity=Decimal("10000"),
            risk_amount=None,
        )

        self.assertIsNone(event.risk_percentage)
