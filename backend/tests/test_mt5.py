import unittest
from datetime import UTC, datetime
from decimal import Decimal

from trade_coach.domain import CloseReason, TradeSide, PositionClosed
from trade_coach.mt5 import (
    Mt5Deal,
    Mt5DealEntry,
    position_closed_from_deals,
)

def make_mt5_deal(
        *,
        deal_id: str = "deal-open",
        position_id: str = "position-1",
        symbol: str = "XAUUSD",
        occurred_at: datetime = datetime(2026, 8, 2, 8, 0, tzinfo=UTC),
        side: TradeSide = TradeSide.BUY,
        reason: CloseReason = CloseReason.STOP_LOSS,
        volume: Decimal = Decimal("0.10"),
        price: Decimal = Decimal("4046.21"),
        commission: Decimal = Decimal("-1"),
        swap: Decimal = Decimal("2"),
        fee: Decimal = Decimal("1"),
        profit: Decimal = Decimal("100"),
        entry: Mt5DealEntry = Mt5DealEntry.IN,
) -> Mt5Deal:
    return Mt5Deal(
        deal_id=deal_id,
        position_id=position_id,
        symbol=symbol,
        occurred_at=occurred_at,
        side=side,
        reason=reason,
        volume=volume,
        price=price,
        commission=commission,
        swap=swap,
        fee=fee,
        profit=profit,
        entry=entry,
    )
    

class PositionClosedFromDealsTests(unittest.TestCase):
    def test_builds_closed_position_from_open_and_close_deals(self) -> None:
        open_deal = make_mt5_deal(
            symbol="EURUSD",
            reason=CloseReason.OTHER,
            price=Decimal("1.15000"),
            swap=Decimal("0"),
            fee=Decimal("-0.5"),
            profit=Decimal("0"),
        )

        close_deal = make_mt5_deal(
            deal_id="deal-close",
            symbol="EURUSD",
            occurred_at=datetime(2026, 8, 2, 10, 30, tzinfo=UTC),
            side=TradeSide.SELL,
            reason=CloseReason.STOP_LOSS,
            price=Decimal("1.14500"),
            swap=Decimal("-2"),
            fee=Decimal("-0.5"),
            profit=Decimal("-50"),
            entry=Mt5DealEntry.OUT,
        )

        position = position_closed_from_deals(
            account_id="account-1",
            deals=(open_deal, close_deal),
        )

        self.assertEqual(position.account_id, "account-1")
        self.assertEqual(position.position_id, "position-1")
        self.assertEqual(position.event_id, "deal-close")
        self.assertEqual(position.symbol, "EURUSD")
        self.assertEqual(position.side, TradeSide.BUY)
        self.assertEqual(position.occurred_at, close_deal.occurred_at)
        self.assertEqual(position.close_price, Decimal("1.14500"))
        self.assertEqual(position.close_reason, CloseReason.STOP_LOSS)

        self.assertEqual(position.profit, Decimal("-50"))
        self.assertEqual(position.commission, Decimal("-2"))
        self.assertEqual(position.swap, Decimal("-2"))
        self.assertEqual(position.fee, Decimal("-1.00"))
        self.assertEqual(position.net_profit, Decimal("-55.00"))

    def test_rejects_deals_from_different_positions(self) -> None:
        open_deal = make_mt5_deal(
            symbol="EURUSD",
            reason=CloseReason.OTHER,
            price=Decimal("1.15000"),
            swap=Decimal("0"),
            fee=Decimal("-0.5"),
            profit=Decimal("0"),
        )

        close_deal = make_mt5_deal(
            deal_id="deal-close",
            position_id="position-2",
            symbol="EURUSD",
            occurred_at=datetime(2026, 8, 2, 10, 30, tzinfo=UTC),
            side=TradeSide.SELL,
            reason=CloseReason.STOP_LOSS,
            price=Decimal("1.14500"),
            swap=Decimal("-2"),
            fee=Decimal("-0.5"),
            profit=Decimal("-50"),
            entry=Mt5DealEntry.OUT,
        )

        with self.assertRaisesRegex(
            ValueError,
            "All deals must belong to the same position!",
        ):
            position_closed_from_deals(
            account_id="account-1",
            deals=(open_deal, close_deal),
        )

    def test_rejects_empty_deals(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "deals must not be empty !",
        ):
            position_closed_from_deals(
                account_id="account-1",
                deals=(),
            )
    def test_rejects_deals_without_opening_deal(self) -> None:
        return None