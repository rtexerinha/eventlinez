import logging
import threading

from eventlinez.celery import app
from order.models import Order

logger = logging.getLogger(__name__)


@app.task()
def send_mail(order_id):
    logger.info("Sending confirmation email for order %s" % order_id)
    order = Order.objects.get(pk=order_id)
    order.send_notification()
    logger.info("Email sent successfully for order %s" % order_id)


def send_mail_async(order_id):
    """
    Send the confirmation email in a background thread so the purchase
    response is returned to the customer immediately, without waiting for
    PDF generation + SMTP round-trip to complete.
    """
    def _run():
        try:
            send_mail(order_id)
        except Exception as e:
            logger.error("Background email failed for order %s: %s" % (order_id, e), exc_info=True)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
