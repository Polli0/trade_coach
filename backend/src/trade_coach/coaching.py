from trade_coach.domain import CoachMessage, PositionOpened, TradingPlan


def create_risk_message(position: PositionOpened, plan: TradingPlan) -> CoachMessage | None:
    return None