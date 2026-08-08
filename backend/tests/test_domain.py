import unittest
from datetime import UTC, datetime
from decimal import Decimal

from trade_coach.domain import PositionOpened, TradeSide, TradingPlan


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


class TradingPlanTests(unittest.TestCase):
    def test_rejects_non_positive_max_risk_percentage(self) -> None:
        invalid_risk = (
            Decimal("0"),
            Decimal("-0.01"),
        )

        for max_risk_percentage in invalid_risk:
            with self.subTest(max_risk_percentage = max_risk_percentage):
                with self.assertRaisesRegex(
                    ValueError,
                    "max risk percentage must be greater than zero",
                ):
                    TradingPlan(
                        account_id = "account-1",
                        max_risk_percentage = max_risk_percentage,
                    )

    def test_detects_when_position_exceeds_risk_limit(self) -> None:
        position = make_position_opened(
            risk_amount=Decimal("200"),
        )
        plan = TradingPlan(
            account_id = "account-1",
            max_risk_percentage = Decimal("1")
        )

        result = plan.is_risk_exceeded_by(position)
        self.assertTrue(result)

    def test_returns_none_when_position_risk_is_unknown(self) -> None:
        position = make_position_opened(
            stop_loss=None,
            risk_amount=None,
        )

        plan = TradingPlan(
            account_id = "account-1",
            max_risk_percentage = Decimal("1"),
        )

        result = plan.is_risk_exceeded_by(position)
        self.assertIsNone(result)

    def test_returns_false_when_position_risk_equals_limit(self) -> None:
        position = make_position_opened(
            risk_amount=Decimal("100"),
        )

        plan = TradingPlan(
            account_id = "account-1",
            max_risk_percentage = Decimal("1"),
        )

        result = plan.is_risk_exceeded_by(position)
        self.assertFalse(result)

    def test_returns_false_when_position_risk_is_below_limit(self) -> None:
        position = make_position_opened(
            risk_amount=Decimal("50"),
        )

        plan = TradingPlan(
            account_id = "account-1",
            max_risk_percentage = Decimal("1"),
        )

        result = plan.is_risk_exceeded_by(position)
        self.assertFalse(result)

    def test_account_not_recognized(self) -> None:
        position = make_position_opened()

        plan = TradingPlan(
            account_id = "account-2",
            max_risk_percentage = Decimal("2"),
        )

        with self.assertRaisesRegex(
            ValueError,
            "position and trading plan must belong to the same account",
        ):

            plan.is_risk_exceeded_by(position)
            