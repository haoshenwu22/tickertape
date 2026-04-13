from rest_framework.response import Response
from rest_framework.views import APIView

from recommendations.services import get_recommendation
from .services import get_stock_history, get_stock_prices, validate_ticker


class StockPricesView(APIView):
    def get(self, request):
        tickers_param = request.query_params.get("tickers", "")
        if not tickers_param:
            return Response({"error": "tickers parameter is required"}, status=400)
        tickers = [t.strip().upper() for t in tickers_param.split(",") if t.strip()]
        prices = get_stock_prices(tickers)
        return Response(prices)


class StockHistoryView(APIView):
    def get(self, request):
        ticker = request.query_params.get("ticker", "").upper()
        period = request.query_params.get("period", "1mo")
        if not ticker:
            return Response({"error": "ticker parameter is required"}, status=400)
        if period not in ("1w", "1mo", "3mo", "1y"):
            period = "1mo"
        # yfinance uses "5d" instead of "1w"
        yf_period = "5d" if period == "1w" else period
        history = get_stock_history(ticker, yf_period)
        return Response(history)


class StockRecommendationView(APIView):
    def get(self, request):
        ticker = request.query_params.get("ticker", "").upper()
        if not ticker:
            return Response({"error": "ticker parameter is required"}, status=400)
        prices = get_stock_prices([ticker])
        stock = prices.get(ticker, {})
        rec = get_recommendation(
            ticker, stock.get("price", 0), stock.get("change_pct", 0)
        )
        return Response(rec)


class ValidateTickerView(APIView):
    def get(self, request):
        ticker = request.query_params.get("ticker", "").upper()
        if not ticker:
            return Response({"error": "ticker parameter is required"}, status=400)
        is_valid = validate_ticker(ticker)
        return Response({"ticker": ticker, "valid": is_valid})
