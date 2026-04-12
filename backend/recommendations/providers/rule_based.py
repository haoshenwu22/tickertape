from .base import RecommendationProvider


class RuleBasedProvider(RecommendationProvider):
    """Simple rule-based fallback when AI providers are unavailable."""

    def get_recommendation(self, ticker: str, price: float, change_pct: float) -> dict:
        if change_pct > 3:
            return {"action": "Sell", "reason": f"{ticker} is up {change_pct:.1f}% — consider taking profits."}
        elif change_pct < -3:
            return {"action": "Buy", "reason": f"{ticker} is down {change_pct:.1f}% — potential buying opportunity."}
        else:
            return {"action": "Hold", "reason": f"{ticker} is relatively stable at {change_pct:+.1f}% change."}
