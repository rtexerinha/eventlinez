from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from ticket.models import Ticket
from django.template.loader import render_to_string
from django.core.mail import EmailMessage


# @receiver(post_save, sender=User)
# def user_saved(sender, instance, **kwargs):
#     if kwargs.get('created', False):
#         # current_date = datetime.now(pytz.utc)
#         unsent_tickets = Ticket.objects.filter(email=instance.username, account_required=True)
#
#         for freeticket in unsent_tickets:
#             message = render_to_string('freeticket/email/freeticket-email.html',
#                                        {'freeticket': freeticket, 'user': freeticket.guest_name})
#
#             email_free_ticket = EmailMessage(
#                 subject="Eventlinez - New Free Ticket",
#                 body=message,
#                 from_email='noreply@eventlinez.com',
#                 to=[instance.username],
#             )
#             email_free_ticket.content_subtype = "html"
#
#             output_pdf = freeticket.as_pdf()
#             email_free_ticket.attach('ticket_{}.pdf'.format(freeticket.id), output_pdf, 'application/pdf')
#
#             email_free_ticket.send()
#             freeticket.is_email_sent = True
#             freeticket.save()
