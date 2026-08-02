import unittest
from datetime import UTC, datetime
from decimal import Decimal

from trade_coach.domain import PositionOpened, TradeSide


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


class PositionOpenedTests(unittest.TestCase):
    def test_calculates_risk_percentage(self) -> None:
        event = make_position_opened()

        self.assertEqual(event.risk_percentage, Decimal("1"))

    def test_returns_none_when_risk_amount_is_missing(self) -> None:
        event = make_position_opened(
            stop_loss=None,
            risk_amount=None,
        )

        self.assertIsNone(event.risk_percentage)

    def test_rejects_zero_equity(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "equity must be greater than zero",
        ):
            make_position_opened(equity=Decimal("0"))

    def test_rejects_non_positive_volume(self) -> None:
        invalid_volumes = (
            Decimal("0"),
            Decimal("-0.01"),
        )

        for volume in invalid_volumes:
            with self.subTest(volume=volume):
                with self.assertRaisesRegex(
                    ValueError,
                    "volume must be greater than zero",
                ):
                    make_position_opened(volume=volume)
