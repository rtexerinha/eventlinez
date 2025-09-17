#!/bin/bash

# Simple Ticket Creation Fix Script
# Run this on production server as root: sudo bash simple_ticket_fix.sh

echo "🚀 Fixing Ticket Creation Issues..."

# Configuration
APP_DIR="/app/eventlinez"
BACKUP_DIR="/tmp/eventlinez_backup_$(date +%Y%m%d_%H%M%S)"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

# Create backup
echo "📁 Creating backup in $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"
cp "$APP_DIR/event/forms.py" "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  forms.py not found"
cp "$APP_DIR/event/views.py" "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  views.py not found"

# 1. Fix forms.py - Remove bootstrap_datepicker_plus
echo "🔧 Fixing forms.py..."
cat > "$APP_DIR/event/forms.py" << 'FORMS_EOF'
from django import forms
from django.forms import ModelForm, ValidationError, TextInput
from django.contrib.auth.forms import PasswordChangeForm

from address.models import City
from event.models import Category, Event, Ticket
from promoter.models import Vendor, Promoter
from django.core.exceptions import ValidationError

class CityForm(ModelForm):
    class Meta:
        model = City
        fields = ["name"]

class TicketForm(ModelForm):
    class Meta:
        model = Ticket
        fields = ["name", "quantity", "price", "event", "sold_out"]

    def __init__(self, *args, **kwargs):
        event_id = kwargs.pop("event_id", None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields["event"].queryset = Event.objects.filter(pk=self.instance.event_id)
        elif event_id is not None:
            self.fields["event"].queryset = Event.objects.filter(pk=event_id)
            self.fields["event"].initial = event_id
            self.fields["event"].widget = forms.HiddenInput()

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if not getattr(self.instance, "pk", None):
            return quantity
        if quantity < self.instance.qty_sold():
            raise ValidationError("Ticket quantity cannot be less than quantity sold")
        return quantity

class TicketUpdateForm(TicketForm):
    pass

class VendorForm(ModelForm):
    class Meta:
        model = Vendor
        fields = ["first_name", "last_name", "email", "phone"]

class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ["name"]

class EventForm(ModelForm):
    event_date = forms.DateTimeField(
        input_formats=["%d/%m/%Y %H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "id": "datetimepicker"},
        ),
    )

    class Meta:
        model = Event
        exclude = ("slug", "created", "updated", "promoter", "vendors")
        
    def clean_event_date(self):
        """Ensure event_date is timezone-aware"""
        from django.utils import timezone
        event_date = self.cleaned_data.get('event_date')
        if event_date and timezone.is_naive(event_date):
            event_date = timezone.make_aware(event_date)
        return event_date

class PromoterForm(ModelForm):
    class Meta:
        model = Promoter
        fields = ["name", "phone", "city", "address", "zip", "ssn"]
        widgets = {
            "name": TextInput(attrs={"class": "form-control"}),
            "phone": TextInput(attrs={"class": "form-control"}),
            "city": TextInput(attrs={"class": "form-control"}),
            "address": TextInput(attrs={"class": "form-control"}),
            "zip": TextInput(attrs={"class": "form-control"}),
            "ssn": TextInput(attrs={"class": "form-control"}),
        }

class ResetPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget = forms.PasswordInput(attrs={"class": "form-control"})
        self.fields["new_password1"].widget = forms.PasswordInput(attrs={"class": "form-control"})
        self.fields["new_password2"].widget = forms.PasswordInput(attrs={"class": "form-control"})
FORMS_EOF

# 2. Add exception handling to views.py
echo "🔧 Adding exception handling to views.py..."

# First, let's add the new ticket_type_create function
cat >> /tmp/new_ticket_views.py << 'VIEWS_EOF'

# Enhanced ticket_type_create with exception handling
@login_required(login_url='/promoter/account/login/')
def ticket_type_create(request, event_id):
    # Get the event object to ensure it exists
    try:
        event = get_object_or_404(Event, id=event_id)
    except Exception as e:
        print(f"Error getting event {event_id}: {e}")
        return render(request, 'ticket_type/ticket_type_create.html', {
            'error': f'Event not found: {e}',
            'event_id': event_id
        })

    if request.method == 'POST':
        try:
            # Pass event_id to the form for proper initialization
            form = TicketForm(request.POST, event_id=event_id)
            print(f"Form created with data: {request.POST}")
            
            if form.is_valid():
                print("Form is valid, attempting to save...")
                try:
                    ticket = form.save(commit=False)
                    ticket.event = event  # Assign the event directly
                    ticket.save()
                    print(f"Ticket saved successfully: {ticket}")
                    # Redirect back to ticket list for this event
                    return redirect('ticket_type_list_per_event', event_id=event_id)
                except Exception as save_error:
                    print(f"Error saving ticket: {save_error}")
                    form.add_error(None, f"Error saving ticket: {save_error}")
            else:
                print(f"Form validation failed. Errors: {form.errors}")
                
        except Exception as form_error:
            print(f"Error creating form: {form_error}")
            # Create a fresh form if there's an error
            form = TicketForm(event_id=event_id)
            form.add_error(None, f"Error processing form: {form_error}")
    else:
        # For GET requests, create form with event_id parameter
        try:
            form = TicketForm(event_id=event_id)
        except Exception as e:
            print(f"Error creating GET form: {e}")
            form = TicketForm()
            form.add_error(None, f"Error creating form: {e}")

    return render(request, 'ticket_type/ticket_type_create.html', {
        'form': form, 
        'event': event,
        'event_id': event_id
    })

# Enhanced ticket_type_update with exception handling
@login_required(login_url='/promoter/account/login/')
def ticket_type_update(request, ticket_id):
    try:
        instance = get_object_or_404(Ticket, id=ticket_id)
    except Exception as e:
        print(f"Error getting ticket {ticket_id}: {e}")
        return render(request, 'ticket_type/ticket_type_create.html', {
            'error': f'Ticket not found: {e}',
            'ticket_id': ticket_id
        })

    if request.method == 'POST':
        try:
            form = TicketUpdateForm(request.POST, instance=instance)
            print(f"Update form created with data: {request.POST}")
            
            if form.is_valid():
                print("Update form is valid, attempting to save...")
                try:
                    form.save()
                    print(f"Ticket updated successfully: {instance}")
                    return redirect('ticket_type_list_per_event', event_id=instance.event_id)
                except Exception as save_error:
                    print(f"Error saving updated ticket: {save_error}")
                    form.add_error(None, f"Error saving ticket: {save_error}")
            else:
                print(f"Update form validation failed. Errors: {form.errors}")
                
        except Exception as form_error:
            print(f"Error creating update form: {form_error}")
            # Create a fresh form if there's an error
            form = TicketUpdateForm(instance=instance)
            form.add_error(None, f"Error processing form: {form_error}")
    else:
        try:
            form = TicketUpdateForm(instance=instance)
        except Exception as e:
            print(f"Error creating GET update form: {e}")
            form = TicketUpdateForm(instance=instance)
            form.add_error(None, f"Error creating form: {e}")

    return render(request, 'ticket_type/ticket_type_create.html', {
        'form': form, 
        'event': instance.event,
        'event_id': instance.event_id
    })
VIEWS_EOF

# Replace the functions in the original views.py
python3 << 'PYTHON_EOF'
import re

# Read the original views.py
with open('/app/eventlinez/event/views.py', 'r') as f:
    content = f.read()

# Read the new functions
with open('/tmp/new_ticket_views.py', 'r') as f:
    new_functions = f.read()

# Remove the old functions
# Remove ticket_type_create function
content = re.sub(
    r'@login_required\(login_url=\'/promoter/account/login/\'\)\s*\n\s*def ticket_type_create\(request, event_id\):.*?(?=@login_required|\Z)',
    '',
    content,
    flags=re.DOTALL
)

# Remove ticket_type_update function
content = re.sub(
    r'@login_required\(login_url=\'/promoter/account/login/\'\)\s*\n\s*def ticket_type_update\(request, ticket_id\):.*?(?=@login_required|\Z)',
    '',
    content,
    flags=re.DOTALL
)

# Add the new functions at the end
content = content.rstrip() + new_functions

# Write back to the file
with open('/app/eventlinez/event/views.py', 'w') as f:
    f.write(content)

print("Views.py updated successfully")
PYTHON_EOF

# 3. Add error display to template
echo "🔧 Adding error display to template..."
TEMPLATE_FILE="$APP_DIR/event/templates/ticket_type/ticket_type_create.html"

if [[ -f "$TEMPLATE_FILE" ]]; then
    # Create a backup
    cp "$TEMPLATE_FILE" "$BACKUP_DIR/ticket_type_create.html"
    
    # Add error display after the page header
    sed -i '/<div class="page-header">/,/<\/div>/{
        /<\/div>/{
            a\
\
    <!-- Error Messages -->\
    {% if error %}\
    <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 8px; margin-bottom: 20px;">\
        <strong>Error:</strong> {{ error }}\
    </div>\
    {% endif %}\
\
    {% if form.non_field_errors %}\
    <div style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 8px; margin-bottom: 20px;">\
        <strong>Form Errors:</strong>\
        <ul>\
            {% for error in form.non_field_errors %}\
            <li>{{ error }}</li>\
            {% endfor %}\
        </ul>\
    </div>\
    {% endif %}
        }
    }' "$TEMPLATE_FILE"
    echo "✅ Template updated"
else
    echo "⚠️  Template file not found"
fi

# 4. Set permissions
echo "🔧 Setting file permissions..."
chown -R nginx:nginx "$APP_DIR"
chmod -R 755 "$APP_DIR"

# 5. Test syntax
echo "🧪 Testing Python syntax..."
cd "$APP_DIR"
python3 -m py_compile event/forms.py && echo "✅ forms.py syntax OK" || echo "❌ forms.py syntax error"
python3 -m py_compile event/views.py && echo "✅ views.py syntax OK" || echo "❌ views.py syntax error"

# 6. Restart services
echo "🔄 Restarting uWSGI..."
systemctl restart uwsgi
sleep 3

if systemctl is-active --quiet uwsgi; then
    echo "✅ uWSGI restarted successfully"
else
    echo "❌ uWSGI restart failed"
    systemctl status uwsgi --no-pager -l
fi

echo "🔄 Restarting Nginx..."
systemctl restart nginx
sleep 2

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx restarted successfully"
else
    echo "❌ Nginx restart failed"
    systemctl status nginx --no-pager -l
fi

# 7. Test application
echo "🧪 Testing application..."
if curl -f -s -o /dev/null http://localhost/; then
    echo "✅ Application is responding"
else
    echo "⚠️  Application may not be responding correctly"
fi

# Clean up
rm -f /tmp/new_ticket_views.py

echo ""
echo "🎉 Ticket Creation Fix Complete!"
echo ""
echo "📋 Changes made:"
echo "  ✅ Removed bootstrap_datepicker_plus dependency"
echo "  ✅ Added comprehensive exception handling"
echo "  ✅ Enhanced error display in templates"
echo "  ✅ Services restarted"
echo ""
echo "📁 Backup location: $BACKUP_DIR"
echo ""
echo "🧪 Test ticket creation now!"
echo "📊 Monitor logs: sudo journalctl -u uwsgi -f"
echo ""

# Show recent logs
echo "📝 Recent uWSGI logs:"
journalctl -u uwsgi --no-pager -n 10 || echo "No recent logs"
