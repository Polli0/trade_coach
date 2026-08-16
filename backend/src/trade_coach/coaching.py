from trade_coach.domain import CoachMessage, PositionOpened, TradingPlan, RiskEvaluation, CoachMessageKind



def create_risk_message(position: PositionOpened, plan: TradingPlan) -> CoachMessage | None:
    evaluation = plan.evaluate_risk(position)
    if evaluation is RiskEvaluation.EXCEEDED:
        return CoachMessage (
            account_id=position.account_id,
            position_id=position.position_id,
            occurred_at=position.occurred_at,
            kind=CoachMessageKind.RISK_LIMIT_EXCEEDED,
            title= "Rischio massimo superato",
            body=(
                f"Il rischio della posizione ({position.risk_percentage}%) "
                f"supera il limite del piano ({plan.max_risk_percentage}%)."
            ),
        )

    if evaluation is RiskEvaluation.UNKNOWN:
        return CoachMessage (
            account_id=position.account_id,
            position_id=position.position_id,
            occurred_at=position.occurred_at,
            kind= CoachMessageKind.RISK_UNKNOWN,
            title= "Rischio sconosciuto",
            body= (
                "Il rischio della posizione è sconosciuto. "
                "ATTENZIONE. E' buon norma inserire gli stop-loss. "
            ),
        )

    return None