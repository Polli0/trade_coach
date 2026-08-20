from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from datetime import datetime

from trade_coach.domain import CloseReason, TradeSide, PositionClosed

class Mt5DealEntry(StrEnum):
    IN = "in"
    OUT = "out"

@dataclass(frozen=True, slots=True)
class Mt5Deal:
    deal_id: str
    position_id: str
    symbol: str
    occurred_at: datetime
    side: TradeSide
    reason: CloseReason
    volume: Decimal
    price: Decimal
    commission: Decimal
    swap: Decimal
    fee: Decimal
    profit: Decimal
    entry: Mt5DealEntry

def position_closed_from_deals(*, account_id: str, deals: tuple[Mt5Deal, ...]) -> PositionClosed:
    open_deals: list[Mt5Deal] = []
    close_deals: list[Mt5Deal] = []

    for x in deals:
        if x.entry is Mt5DealEntry.IN:
            open_deals.append(x)
        else:
            close_deals.append(x)

    total_profit = Decimal("0")
    total_commission = Decimal("0")
    total_swap = Decimal("0")
    total_fee = Decimal("0")

    open_deals = sorted(open_deals, key=lambda x: x.occurred_at)
    close_deals = sorted(close_deals, key=lambda x: x.occurred_at)

    for x in open_deals:
        total_profit += x.profit
        total_commission += x.commission
        total_swap += x.swap
        total_fee += x.fee

    for x in close_deals:
        total_profit += x.profit
        total_commission += x.commission
        total_swap += x.swap
        total_fee += x.fee

    final_open_deal = open_deals[0]
    final_close_deal = close_deals[-1]

    return PositionClosed(
        event_id=final_close_deal.deal_id,
        account_id=account_id,
        position_id=final_close_deal.position_id,
        occurred_at=final_close_deal.occurred_at,
        symbol=final_close_deal.symbol,
        side=final_open_deal.side,
        profit=total_profit,
        commission=total_commission,
        close_price=final_close_deal.price,
        swap=total_swap,
        fee=total_fee,
        close_reason=final_close_deal.reason,        
    )

