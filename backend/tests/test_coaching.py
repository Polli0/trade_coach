import unittest
from datetime import UTC, datetime
from decimal import Decimal

from trade_coach.coaching import create_risk_message
from trade_coach.domain import CoachMessageKind, PositionOpened, TradeSide, TradingPlan

class RiskMessageTests(unittest.TestCase):
    def test_creates_message_when_risk_limit_is_exceeded(self) -> None:
        return None