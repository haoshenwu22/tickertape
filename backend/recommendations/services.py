import logging

from django.conf import settings
from django.core.cache import cache

from .providers.claude import ClaudeProvider
from .providers.rule_based import RuleBasedProvider

logger = logging.getLogger(__name__)

# Provider registry — add new providers here
PROVIDERS = {
    "claude": ClaudeProvider,
    "rule_based": RuleBasedProvider,
    # Future: "kimi": KimiProvider, "deepseek": DeepSeekProvider
}


def _get_provider():
    provider_name = getattr(settings, "AI_RECOMMENDATION_PROVIDER", "claude")
    provider_class = PROVIDERS.get(provider_name)
    if provider_class is None:
        logger.warning(f"Unknown provider '{provider_name}', falling back to rule_based")
        provider_class = RuleBasedProvider
    return provider_class()


def get_recommendation(ticker: str, price: float, change_pct: float) -> dict:
    """Get AI recommendation with caching and fallback."""
    from datetime import datetime

    now = datetime.now()
    cache_key = f"rec:{ticker}:{now.strftime('%Y-%m-%d')}:{now.hour}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    provider = _get_provider()
    try:
        result = provider.get_recommendation(ticker, price, change_pct)
    except Exception:
        logger.warning(f"Primary provider failed for {ticker}, using rule-based fallback")
        fallback = RuleBasedProvider()
        result = fallback.get_recommendation(ticker, price, change_pct)

    # Validate result structure
    if result.get("action") not in ("Buy", "Hold", "Sell"):
        result["action"] = "Hold"
    if not result.get("reason"):
        result["reason"] = "No analysis available."

    cache.set(cache_key, result, timeout=3600)  # 1 hour TTL
    return result
