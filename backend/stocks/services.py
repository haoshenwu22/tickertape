import logging

import yfinance as yf

logger = logging.getLogger(__name__)

# Mock data used when yfinance is unavailable
MOCK_PRICES = {
    "AAPL": {"price": 178.50, "name": "Apple Inc.", "change_pct": 1.2, "currency": "USD"},
    "GOOGL": {"price": 141.80, "name": "Alphabet Inc.", "change_pct": -0.5, "currency": "USD"},
    "MSFT": {"price": 378.90, "name": "Microsoft Corp.", "change_pct": 0.8, "currency": "USD"},
    "AMZN": {"price": 178.25, "name": "Amazon.com Inc.", "change_pct": 2.1, "currency": "USD"},
    "TSLA": {"price": 245.60, "name": "Tesla Inc.", "change_pct": -1.3, "currency": "USD"},
}


def validate_ticker(symbol: str) -> bool:
    """Check if a ticker symbol is valid by querying yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info.get("regularMarketPrice") is not None or info.get("currentPrice") is not None
    except Exception:
        logger.warning(f"yfinance validation failed for {symbol}, checking mock data")
        return symbol.upper() in MOCK_PRICES


def get_stock_prices(tickers: list[str]) -> dict:
    """Batch-fetch current prices for a list of ticker symbols."""
    result = {}
    try:
        data = yf.Tickers(" ".join(tickers))
        for symbol in tickers:
            symbol = symbol.upper()
            try:
                ticker = data.tickers[symbol]
                info = ticker.info
                price = info.get("regularMarketPrice") or info.get("currentPrice") or 0
                prev_close = info.get("previousClose") or price
                change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
                result[symbol] = {
                    "price": round(price, 2),
                    "name": info.get("shortName", symbol),
                    "change_pct": round(change_pct, 2),
                    "currency": info.get("currency", "USD"),
                    "is_mock": False,
                }
            except Exception:
                result[symbol] = _get_mock_price(symbol)
    except Exception:
        logger.warning("yfinance batch fetch failed, using mock data")
        for symbol in tickers:
            result[symbol.upper()] = _get_mock_price(symbol.upper())
    return result


def get_stock_history(ticker: str, period: str = "1mo") -> list[dict]:
    """Get historical price data for charting."""
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period=period)
        return [
            {
                "date": index.strftime("%Y-%m-%d"),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            }
            for index, row in hist.iterrows()
        ]
    except Exception:
        logger.warning(f"yfinance history failed for {ticker}")
        return []


def _get_mock_price(symbol: str) -> dict:
    """Return mock price data for a symbol."""
    mock = MOCK_PRICES.get(symbol, {
        "price": 100.00, "name": symbol, "change_pct": 0.0, "currency": "USD",
    })
    return {**mock, "is_mock": True}
