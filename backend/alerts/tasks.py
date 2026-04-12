import logging
from datetime import timezone

from celery import shared_task
from django.utils import timezone as dj_timezone

logger = logging.getLogger(__name__)


@shared_task
def check_price_alerts():
    """Check all active price alerts and trigger any that match."""
    from django.core.mail import send_mail
    from django.conf import settings

    from stocks.services import get_stock_prices
    from .models import PriceAlert

    active_alerts = PriceAlert.objects.filter(is_triggered=False)
    if not active_alerts.exists():
        return

    # Get unique tickers
    tickers = list(active_alerts.values_list("ticker", flat=True).distinct())
    prices = get_stock_prices(tickers)

    triggered = []
    for alert in active_alerts:
        stock = prices.get(alert.ticker, {})
        current_price = stock.get("price", 0)
        if not current_price:
            continue

        should_trigger = (
            (alert.condition == "above" and current_price >= float(alert.target_price))
            or (alert.condition == "below" and current_price <= float(alert.target_price))
        )

        if should_trigger:
            alert.is_triggered = True
            alert.triggered_at = dj_timezone.now()
            alert.save()
            triggered.append((alert, current_price))

    # Send alert emails
    for alert, current_price in triggered:
        try:
            send_mail(
                subject=f"TickerTape Alert: {alert.ticker} is now ${current_price:.2f}",
                message=(
                    f"Your price alert for {alert.ticker} has been triggered!\n\n"
                    f"Condition: {alert.condition} ${alert.target_price}\n"
                    f"Current Price: ${current_price:.2f}\n\n"
                    f"— TickerTape"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[alert.user.email],
            )
        except Exception as e:
            logger.error(f"Failed to send alert email for {alert}: {e}")

    if triggered:
        logger.info(f"Triggered {len(triggered)} price alert(s)")
