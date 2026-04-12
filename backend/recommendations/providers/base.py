from abc import ABC, abstractmethod


class RecommendationProvider(ABC):
    @abstractmethod
    def get_recommendation(self, ticker: str, price: float, change_pct: float) -> dict:
        """
        Returns a recommendation dict:
        {
            "action": "Buy" | "Hold" | "Sell",
            "reason": "Short explanation string"
        }
        """
