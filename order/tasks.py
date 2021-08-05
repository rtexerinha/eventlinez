import logging

from eventlinez.celery import app
from order.models import Order, OrderItem

logger = logging.getLogger(__name__)


@app.task()
def send_mail(order_id):
    logger.info("Enviando email da order %s" % order_id)
    order = Order.objects.get(pk=order_id)
    item_order = OrderItem.objects.get(order=order_id)
    order.send_notification(item_order)
    logger.info("Email enviado com sucesso ")
