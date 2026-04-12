import logging
from collections import defaultdict

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from recommendations.services import get_recommendation
from stocks.services import get_stock_prices
from subscriptions.models import Subscription

logger = logging.getLogger(__name__)


def send_stock_email_for_subscription(subscription):
    """Send a single stock price email for one subscription (Send Now)."""
    prices = get_stock_prices([subscription.ticker])
    stock = prices.get(subscription.ticker, {})
    rec = get_recommendation(
        subscription.ticker,
        stock.get("price", 0),
        stock.get("change_pct", 0),
    )

    stocks_data = [{
        "ticker": subscription.ticker,
        "name": stock.get("name", subscription.ticker),
        "price": stock.get("price", "N/A"),
        "change_pct": stock.get("change_pct", 0),
        "currency": stock.get("currency", "USD"),
        "action": rec.get("action", "Hold"),
        "reason": rec.get("reason", ""),
    }]

    _send_email(subscription.email, stocks_data)


def send_merged_emails():
    """Send periodic emails, merging multiple tickers per email address."""
    subscriptions = Subscription.objects.all()
    if not subscriptions.exists():
        logger.info("No subscriptions to send emails for.")
        return

    # Group subscriptions by email
    email_tickers = defaultdict(set)
    for sub in subscriptions:
        email_tickers[sub.email].add(sub.ticker)

    # Fetch all unique tickers at once
    all_tickers = list({t for tickers in email_tickers.values() for t in tickers})
    prices = get_stock_prices(all_tickers)

    # Get recommendations for each ticker
    recommendations = {}
    for ticker in all_tickers:
        stock = prices.get(ticker, {})
        recommendations[ticker] = get_recommendation(
            ticker, stock.get("price", 0), stock.get("change_pct", 0)
        )

    # Send one email per unique email address
    for email, tickers in email_tickers.items():
        stocks_data = []
        for ticker in sorted(tickers):
            stock = prices.get(ticker, {})
            rec = recommendations.get(ticker, {})
            stocks_data.append({
                "ticker": ticker,
                "name": stock.get("name", ticker),
                "price": stock.get("price", "N/A"),
                "change_pct": stock.get("change_pct", 0),
                "currency": stock.get("currency", "USD"),
                "action": rec.get("action", "Hold"),
                "reason": rec.get("reason", ""),
            })
        _send_email(email, stocks_data)

    logger.info(f"Sent merged emails to {len(email_tickers)} recipients covering {len(all_tickers)} tickers.")


def _send_email(to_email: str, stocks_data: list[dict]):
    """Render and send the stock price email."""
    subject = "TickerTape: Your Stock Price Update"
    html_message = render_to_string("notifications/stock_email.html", {"stocks": stocks_data})
    plain_message = _render_plain(stocks_data)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
        )
        logger.info(f"Email sent to {to_email} with {len(stocks_data)} stock(s)")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")


def _render_plain(stocks_data: list[dict]) -> str:
    """Plain-text fallback for email clients that don't support HTML."""
    lines = ["TickerTape Stock Price Update", "=" * 40, ""]
    for s in stocks_data:
        lines.append(f"{s['ticker']} ({s['name']}): ${s['price']} ({s['change_pct']:+.2f}%)")
        lines.append(f"  Recommendation: {s['action']} — {s['reason']}")
        lines.append("")
    lines.append("Disclaimer: For demo purposes only — not financial advice.")
    return "\n".join(lines)
