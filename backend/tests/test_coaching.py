import unittest
from datetime import UTC, datetime
from decimal import Decimal

from trade_coach.coaching import create_risk_message, create_trade_after_stop_loss_message
from trade_coach.domain import (
    CloseReason,
    CoachMessageKind,
    DailySummary,
    PositionClosed,
    PositionOpened,
    TradeSide,
    TradingPlan,
)

def make_position_opened(
    *,
    equity: Decimal = Decimal("10000"),
    risk_amount: Decimal | None = Decimal("100"),
    stop_loss: Decimal | None = Decimal("1.14500"),
    volume: Decimal = Decimal("0.10"),
    account_id: str = "account-1",
    occurred_at: datetime = datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
) -> PositionOpened:
    return PositionOpened(
        event_id="event-1",
        account_id=account_id,
        position_id="position-1",
        occurred_at=occurred_at,
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
    fee: Decimal = Decimal("0"),
    close_reason: CloseReason = CloseReason.OTHER,
    account_id: str = "account-1",
    position_id: str = "position-1",
    occurred_at: datetime = datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
) -> PositionClosed:
    return PositionClosed(
        event_id="event-1",
        account_id=account_id,
        position_id=position_id,
        occurred_at=occurred_at,
        symbol="EURUSD",
        side=TradeSide.BUY,
        profit=profit,
        commission=commission,
        close_price=Decimal("1.17980"),
        swap=swap,
        fee=fee,
        close_reason = close_reason,
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

class TradeAfterStopLossMessageTests(unittest.TestCase):
    def test_creates_message_after_max_losing_stop_losses(self) -> None:
        position1 = make_position_closed(
            profit=Decimal("-100"),
            position_id="position-1",
            occurred_at=datetime(2026, 4, 14, 12, 31, 28, tzinfo=UTC),
            close_reason=CloseReason.STOP_LOSS,
        )

        position2 = make_position_closed(
            profit=Decimal("-100"),
            position_id="position-2",
            occurred_at=datetime(2026, 4, 14, 13, 31, 28, tzinfo=UTC),
            close_reason=CloseReason.STOP_LOSS,
        )

        daily_summary = DailySummary(
            account_id = "account-1",
            day = position1.occurred_at.date(),
            closed_positions = (position1, position2),
        )

        plan = TradingPlan(
            account_id = "account-1",
            max_risk_percentage = Decimal("2"),
            max_daily_stop_losses = 2,
        )

        position3 = make_position_opened(
            occurred_at=datetime(2026, 4, 14, 14, 31, 28, tzinfo=UTC),
        )

        message = create_trade_after_stop_loss_message(position3, daily_summary, plan)

        self.assertIsNotNone(message)
        self.assertIsInstance(message.body, str)
        self.assertEqual(message.kind, CoachMessageKind.TRADE_AFTER_STOP_LOSSES)
        self.assertIn("raggiunto", message.body)

    def test_returns_none_before_reaching_stop_loss_limit(self) -> None:
        position1 = make_position_closed(
            profit=Decimal("-100"),
            occurred_at=datetime(2026, 4, 14, 12, 31, 28, tzinfo=UTC),
            close_reason=CloseReason.STOP_LOSS,
        )
        daily_summary = DailySummary(
            account_id="account-1",
            day=position1.occurred_at.date(),
            closed_positions=(position1,),
        )
        plan = TradingPlan(
            account_id="account-1",
            max_risk_percentage=Decimal("2"),
        )
        new_position = make_position_opened(
            occurred_at=datetime(2026, 4, 14, 14, 31, 28, tzinfo=UTC),
        )

        message = create_trade_after_stop_loss_message(new_position, daily_summary, plan)

        self.assertIsNone(message)

    def test_does_not_count_break_even_or_profitable_stop_loss(self) -> None:
        losing_position = make_position_closed(
            profit=Decimal("-100"),
            position_id="position-1",
            occurred_at=datetime(2026, 4, 14, 12, 31, 28, tzinfo=UTC),
            close_reason=CloseReason.STOP_LOSS,
        )
        profitable_position = make_position_closed(
            profit=Decimal("100"),
            position_id="position-2",
            occurred_at=datetime(2026, 4, 14, 13, 31, 28, tzinfo=UTC),
            close_reason=CloseReason.STOP_LOSS,
        )
        break_even_position = make_position_closed(
            profit=Decimal("5"),
            position_id="position-3",
            occurred_at=datetime(2026, 4, 14, 13, 45, 28, tzinfo=UTC),
            close_reason=CloseReason.STOP_LOSS,
        )
        daily_summary = DailySummary(
            account_id="account-1",
            day=losing_position.occurred_at.date(),
            closed_positions=(
                losing_position,
                profitable_position,
                break_even_position,
            ),
        )
        plan = TradingPlan(
            account_id="account-1",
            max_risk_percentage=Decimal("2"),
        )
        new_position = make_position_opened(
            occurred_at=datetime(2026, 4, 14, 14, 31, 28, tzinfo=UTC),
        )

        message = create_trade_after_stop_loss_message(new_position, daily_summary, plan)

        self.assertIsNone(message)

    def test_does_not_count_stop_loss_after_new_trade(self) -> None:
        position1 = make_position_closed(
            profit=Decimal("-100"),
            position_id="position-1",
            occurred_at=datetime(2026, 4, 14, 12, 31, 28, tzinfo=UTC),
            close_reason=CloseReason.STOP_LOSS,
        )
        position2 = make_position_closed(
            profit=Decimal("-100"),
            position_id="position-2",
            occurred_at=datetime(2026, 4, 14, 15, 31, 28, tzinfo=UTC),
            close_reason=CloseReason.STOP_LOSS,
        )
        daily_summary = DailySummary(
            account_id="account-1",
            day=position1.occurred_at.date(),
            closed_positions=(position1, position2),
        )
        plan = TradingPlan(
            account_id="account-1",
            max_risk_percentage=Decimal("2"),
        )
        new_position = make_position_opened(
            occurred_at=datetime(2026, 4, 14, 14, 31, 28, tzinfo=UTC),
        )

        message = create_trade_after_stop_loss_message(new_position, daily_summary, plan)

        self.assertIsNone(message)

    def test_uses_custom_stop_loss_limit(self) -> None:
        closed_positions = (
            make_position_closed(
                profit=Decimal("-100"),
                position_id="position-1",
                occurred_at=datetime(2026, 4, 14, 11, 31, 28, tzinfo=UTC),
                close_reason=CloseReason.STOP_LOSS,
            ),
            make_position_closed(
                profit=Decimal("-100"),
                position_id="position-2",
                occurred_at=datetime(2026, 4, 14, 12, 31, 28, tzinfo=UTC),
                close_reason=CloseReason.STOP_LOSS,
            ),
        )
        daily_summary = DailySummary(
            account_id="account-1",
            day=closed_positions[0].occurred_at.date(),
            closed_positions=closed_positions,
        )
        plan = TradingPlan(
            account_id="account-1",
            max_risk_percentage=Decimal("2"),
            max_daily_stop_losses=3,
        )
        new_position = make_position_opened(
            occurred_at=datetime(2026, 4, 14, 14, 31, 28, tzinfo=UTC),
        )

        message = create_trade_after_stop_loss_message(new_position, daily_summary, plan)

        self.assertIsNone(message)

    def test_rejects_position_from_different_account(self) -> None:
        daily_summary = DailySummary(
            account_id="account-1",
            day=datetime(2026, 4, 14, tzinfo=UTC).date(),
            closed_positions=(),
        )
        plan = TradingPlan(
            account_id="account-1",
            max_risk_percentage=Decimal("2"),
        )
        new_position = make_position_opened(
            account_id="account-2",
            occurred_at=datetime(2026, 4, 14, 14, 31, 28, tzinfo=UTC),
        )

        with self.assertRaisesRegex(
            ValueError,
            "position, daily summary and trading plan must belong to the same account",
        ):
            create_trade_after_stop_loss_message(new_position, daily_summary, plan)

    def test_rejects_position_from_different_day(self) -> None:
        daily_summary = DailySummary(
            account_id="account-1",
            day=datetime(2026, 4, 14, tzinfo=UTC).date(),
            closed_positions=(),
        )
        plan = TradingPlan(
            account_id="account-1",
            max_risk_percentage=Decimal("2"),
        )
        new_position = make_position_opened(
            occurred_at=datetime(2026, 4, 15, 14, 31, 28, tzinfo=UTC),
        )

        with self.assertRaisesRegex(
            ValueError,
            "position and daily summary must belong to the same day",
        ):
            create_trade_after_stop_loss_message(new_position, daily_summary, plan)
