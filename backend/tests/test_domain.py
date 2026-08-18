import unittest
from datetime import UTC, datetime, date
from decimal import Decimal

from trade_coach.domain import PositionOpened, TradeSide, TradingPlan, RiskEvaluation, PositionClosed, TradeOutcome, CloseReason, DailySummary

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

def make_position_closed(
    *,
    profit: Decimal = Decimal("100"),
    commission: Decimal = Decimal("-3"),
    swap: Decimal = Decimal("-2"),
    close_reason: CloseReason = CloseReason.OTHER,
    position_id: str = "position-1",
    occurred_at: datetime = datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
) -> PositionClosed:
    return PositionClosed(
        event_id="event-1",
        account_id="account-1",
        position_id=position_id,
        occurred_at=occurred_at,
        symbol="EURUSD",
        side=TradeSide.BUY,
        profit=profit,
        commission=commission,
        close_price=Decimal("1.17980"),
        swap=swap,
        close_reason = close_reason,
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

        result = plan.evaluate_risk(position)
        self.assertEqual(result, RiskEvaluation.EXCEEDED)

    def test_returns_unknown_when_position_risk_is_unknown(self) -> None:
        position = make_position_opened(
            stop_loss=None,
            risk_amount=None,
        )

        plan = TradingPlan(
            account_id = "account-1",
            max_risk_percentage = Decimal("1"),
        )

        result = plan.evaluate_risk(position)
        self.assertEqual(result, RiskEvaluation.UNKNOWN)

    def test_returns_within_limit_when_position_risk_equals_limit(self) -> None:
        position = make_position_opened(
            risk_amount=Decimal("100"),
        )

        plan = TradingPlan(
            account_id = "account-1",
            max_risk_percentage = Decimal("1"),
        )

        result = plan.evaluate_risk(position)
        self.assertEqual(result, RiskEvaluation.WITHIN_LIMIT)

    def test_returns_within_limit_when_position_risk_is_below_limit(self) -> None:
        position = make_position_opened(
            risk_amount=Decimal("50"),
        )

        plan = TradingPlan(
            account_id = "account-1",
            max_risk_percentage = Decimal("1"),
        )

        result = plan.evaluate_risk(position)
        self.assertEqual(result, RiskEvaluation.WITHIN_LIMIT)

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

            plan.evaluate_risk(position)

    def test_max_daily_stop_non_positive(self) -> None:
        invalid_max_stop_losses = (
            0,
            -1,
        )

        for max_daily_stop_losses in invalid_max_stop_losses:
            with self.subTest(max_stop_losses = max_daily_stop_losses):
                with self.assertRaisesRegex(
                    ValueError,
                    "max daily stop loss must be greater than zero",
                ):
                    TradingPlan(
                        account_id = "account-1",
                        max_risk_percentage = Decimal("3"),
                        max_daily_stop_losses = max_daily_stop_losses,
                    )

    def test_max_daily_stop_losses_equal_two(self) -> None:
        plan = TradingPlan(
            account_id = "account-1",
            max_risk_percentage = Decimal("2"),
        )

        self.assertEqual(plan.max_daily_stop_losses, 2)

    def test_max_daily_stop_losses_personalized(self) -> None:
        plan = TradingPlan(
            account_id = "account-1",
            max_daily_stop_losses = 3,
            max_risk_percentage = Decimal("2"),
        )

        self.assertEqual(plan.max_daily_stop_losses, 3)

class PositionClosedTests(unittest.TestCase):
    def test_net_profit(self) -> None:
        position_closed = make_position_closed(
            profit=Decimal("100"),
            commission=Decimal("-2"),
            swap=Decimal("-1"),
        )

        self.assertEqual(position_closed.net_profit, Decimal("97"))

    def test_returns_profit_outcome_when_net_profit_is_positive(self) -> None:
        position = make_position_closed(
            profit=Decimal("100"),
            commission=Decimal("-2"),
            swap=Decimal("-1"),
        )

        self.assertEqual(position.outcome, TradeOutcome.PROFIT)

    def test_returns_loss_outcome_when_net_profit_is_negative(self) -> None:
        position = make_position_closed(
            profit=Decimal("-50"),
            commission=Decimal("-2"),
            swap=Decimal("0"),
        )

        self.assertEqual(position.outcome, TradeOutcome.LOSS)

    def test_returns_break_even_outcome_when_net_profit_is_zero(self) -> None:
        position = make_position_closed(
            profit=Decimal("3"),
            commission=Decimal("-2"),
            swap=Decimal("-1"),
        )

        self.assertEqual(position.outcome, TradeOutcome.BREAK_EVEN)

class DailySummaryTests(unittest.TestCase):
    def test_expect_two_daily_stop_loss(self) -> None:
        position1 = make_position_closed(
            close_reason=CloseReason.STOP_LOSS,
        )
        position2 = make_position_closed(
            position_id="position-2",
            close_reason=CloseReason.STOP_LOSS,
        )
        position3 = make_position_closed(
            position_id="position-3",
            close_reason=CloseReason.MANUAL,
        )

        daily_summary = DailySummary(
            account_id = position1.account_id,
            day = position1.occurred_at.date(),
            closed_positions = (position1, position2, position3),
        )

        self.assertEqual(daily_summary.stop_loss_count, 2)

    def test_expect_profit_day(self) -> None:
        position1 = make_position_closed(
            profit = Decimal("100"),
        )
        position2 = make_position_closed(
            profit = Decimal("-52"),
        )
        position3 = make_position_closed(
            profit = Decimal("0"),
        )

        daily_summary = DailySummary(
            account_id = position1.account_id,
            day = position1.occurred_at.date(),
            closed_positions = (position1, position2, position3),
        )

        self.assertEqual(daily_summary.net_profit, Decimal("33"))