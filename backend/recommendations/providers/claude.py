import json
import logging

import anthropic
from django.conf import settings

from .base import RecommendationProvider

logger = logging.getLogger(__name__)


class ClaudeProvider(RecommendationProvider):
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def get_recommendation(self, ticker: str, price: float, change_pct: float) -> dict:
        try:
            message = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Stock: {ticker}, Current Price: ${price:.2f}, "
                            f"Daily Change: {change_pct:+.2f}%.\n\n"
                            "Give a Buy, Hold, or Sell recommendation with a 1-sentence reason. "
                            "This is for demo purposes only, not real financial advice.\n\n"
                            'Respond in JSON: {"action": "Buy|Hold|Sell", "reason": "..."}'
                        ),
                    }
                ],
            )
            text = message.content[0].text.strip()
            # Parse JSON from response (handle markdown code blocks)
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Claude recommendation failed for {ticker}: {e}")
            raise
