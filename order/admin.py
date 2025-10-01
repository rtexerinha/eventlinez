from django.contrib import admin
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponseRedirect
from django import forms
from .models import Order, OrderItem


class OrderItemAdmin(admin.TabularInline):
    model = OrderItem
    fieldsets = [
        ('Ticket', {'fields': ['event_ticket'], }),
        ('Promo Code', {'fields': ['promo_code'], }),
        ('Quantity', {'fields': ['quantity'], }),
        ('Price', {'fields': ['unit_price'], }),
    ]
    readonly_fields = ['ticket', 'quantity', 'unit_price', 'promo_code']
    can_delete = False
    max_num = 0


def resend_confirmation_email(modeladmin, request, queryset):
    """
    Admin action to resend confirmation emails for selected orders
    """
    success_count = 0
    error_count = 0
    
    for order in queryset:
        try:
            # Render the email template
            message = render_to_string('order/email/email.html', {'order': order})
            
            # Create and send the email
            subject = f'Eventlinez - Order Confirmation #{order.id} (Resent)'
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email='noreply@eventlinez.com',
                to=[order.emailAddress],
            )
            email.content_subtype = 'html'
            
            # Attach PDF tickets if they exist
            for item in order.orderitem_set.all():
                for ticket in item.ticket_set.all():
                    try:
                        output_pdf = ticket.as_pdf()
                        email.attach(f'ticket_{ticket.id}.pdf', output_pdf, 'application/pdf')
                    except Exception as e:
                        # Continue if PDF generation fails
                        pass
            
            email.send()
            success_count += 1
            
        except Exception as e:
            error_count += 1
            modeladmin.message_user(
                request, 
                f'Failed to resend email for Order #{order.id}: {str(e)}', 
                level=messages.ERROR
            )
    
    if success_count > 0:
        modeladmin.message_user(
            request, 
            f'Successfully resent {success_count} confirmation email(s).', 
            level=messages.SUCCESS
        )
    
    if error_count > 0:
        modeladmin.message_user(
            request, 
            f'Failed to resend {error_count} email(s). Check the error messages above.', 
            level=messages.WARNING
        )

resend_confirmation_email.short_description = "Resend confirmation email"


class CustomEmailForm(forms.Form):
    email_address = forms.EmailField(
        label='Email Address',
        help_text='Enter the email address to send the confirmation to',
        widget=forms.EmailInput(attrs={'class': 'vTextField', 'placeholder': 'customer@example.com'})
    )
    custom_message = forms.CharField(
        label='Custom Message (Optional)',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50, 'placeholder': 'Add a custom message to the email...'}),
        help_text='Optional: Add a custom message that will be included in the email'
    )


def resend_to_custom_email(modeladmin, request, queryset):
    """
    Admin action to resend confirmation emails to a custom email address
    """
    if queryset.count() != 1:
        modeladmin.message_user(
            request,
            'Please select exactly one order to send to a custom email address.',
            level=messages.ERROR
        )
        return
    
    order = queryset.first()
    
    if request.method == 'POST':
        form = CustomEmailForm(request.POST)
        if form.is_valid():
            email_address = form.cleaned_data['email_address']
            custom_message = form.cleaned_data['custom_message']
            
            try:
                # Render the email template
                message = render_to_string('order/email/email.html', {'order': order})
                
                # Add custom message if provided
                if custom_message:
                    message = message.replace(
                        'Thanks for shopping with us',
                        f'Thanks for shopping with us<br><br><strong>Message from Eventlinez:</strong><br>{custom_message}'
                    )
                
                # Create and send the email
                subject = f'Eventlinez - Order Confirmation #{order.id} (Resent)'
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email='noreply@eventlinez.com',
                    to=[email_address],
                )
                email.content_subtype = 'html'
                
                # Attach PDF tickets if they exist
                for item in order.orderitem_set.all():
                    for ticket in item.ticket_set.all():
                        try:
                            output_pdf = ticket.as_pdf()
                            email.attach(f'ticket_{ticket.id}.pdf', output_pdf, 'application/pdf')
                        except Exception as e:
                            # Continue if PDF generation fails
                            pass
                
                email.send()
                
                modeladmin.message_user(
                    request,
                    f'Confirmation email for Order #{order.id} sent successfully to {email_address}.',
                    level=messages.SUCCESS
                )
                return HttpResponseRedirect(request.get_full_path())
                
            except Exception as e:
                modeladmin.message_user(
                    request,
                    f'Failed to send email: {str(e)}',
                    level=messages.ERROR
                )
    else:
        form = CustomEmailForm(initial={'email_address': order.emailAddress})
    
    context = {
        'form': form,
        'order': order,
        'title': f'Resend Order #{order.id} Confirmation Email',
        'opts': modeladmin.model._meta,
        'has_change_permission': modeladmin.has_change_permission(request),
    }
    
    return render(request, 'admin/order/order/custom_email_form.html', context)

resend_to_custom_email.short_description = "Resend to custom email address"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'emailAddress', 'created']
    list_display_links = ('id', 'emailAddress')
    search_fields = ['id', 'billingName', 'emailAddress']
    readonly_fields = ['id', 'token', 'total', 'emailAddress', 'created', 'billingName', 'billingAddress1',
                       'billingCity', 'billingPostcode', 'billingCountry', 'shippingName', 'shippingAddress1',
                       'shippingCity', 'shippingPostcode', 'shippingCountry']
    fieldsets = [
        ('ORDER INFORMATION', {'fields': ['id', 'token', 'total', 'created', 'emailAddress']}),
    ]
    
    actions = [resend_confirmation_email, resend_to_custom_email]

    inlines = [
        OrderItemAdmin,
    ]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
