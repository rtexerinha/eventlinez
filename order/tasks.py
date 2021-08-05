import logging

from eventlinez.celery import app
from order.models import Order

logger = logging.getLogger(__name__)


@app.task()
def send_mail(order_id, host):
    host = host
    logger.info("Enviando email da order %s" % order_id)
    order = Order.objects.get(pk=order_id)
    order.send_notification(host)
    logger.info("Email enviado com sucesso ")
