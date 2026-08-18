from trade_coach.domain import (
    CloseReason,
    CoachMessage,
    CoachMessageKind,
    DailySummary,
    PositionOpened,
    RiskEvaluation,
    TradeOutcome,
    TradingPlan,
)



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

def create_trade_after_stop_loss_message(
    position: PositionOpened,
    daily_summary: DailySummary,
    plan: TradingPlan,
) -> CoachMessage | None:
    if not (
        position.account_id == daily_summary.account_id == plan.account_id
    ):
        raise ValueError(
            "position, daily summary and trading plan must belong to the same account"
        )

    if position.occurred_at.date() != daily_summary.day:
        raise ValueError("position and daily summary must belong to the same day")

    losing_stop_loss_count = 0

    for closed_position in daily_summary.closed_positions:
        if (
            closed_position.close_reason is CloseReason.STOP_LOSS
            and closed_position.outcome is TradeOutcome.LOSS
            and closed_position.occurred_at < position.occurred_at
        ):
            losing_stop_loss_count += 1

    if losing_stop_loss_count < plan.max_daily_stop_losses:
        return None

    return CoachMessage(
        account_id=position.account_id,
        position_id=position.position_id,
        occurred_at=position.occurred_at,
        kind=CoachMessageKind.TRADE_AFTER_STOP_LOSSES,
        title="Limite giornaliero di stop-loss raggiunto",
        body=(
            f"Hai aperto un trade dopo aver raggiunto il limite giornaliero di "
            f"{plan.max_daily_stop_losses} stop-loss in perdita. "
            "Fermati un momento e verifica che il nuovo ingresso rispetti il tuo piano."
        ),
    )
