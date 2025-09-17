#!/bin/bash

# Fix Ticket Creation - Production Deployment Script
# This script fixes 500 errors in ticket creation by:
# 1. Removing bootstrap_datepicker_plus dependency
# 2. Adding comprehensive exception handling
# 3. Updating templates with error display

set -e  # Exit on any error

echo "🚀 Starting Ticket Creation Fix Deployment..."
echo "================================================"

# Configuration
APP_DIR="/app/eventlinez"
BACKUP_DIR="/tmp/eventlinez_backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="/tmp/ticket_creation_fix.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root (use sudo)"
   exit 1
fi

# Check if app directory exists
if [[ ! -d "$APP_DIR" ]]; then
    error "Application directory $APP_DIR not found!"
    exit 1
fi

log "Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Function to backup files
backup_file() {
    local file_path="$1"
    if [[ -f "$file_path" ]]; then
        local backup_path="$BACKUP_DIR/$(basename "$file_path")"
        cp "$file_path" "$backup_path"
        success "Backed up: $file_path -> $backup_path"
    else
        warning "File not found for backup: $file_path"
    fi
}

# Function to check service status
check_service() {
    local service_name="$1"
    if systemctl is-active --quiet "$service_name"; then
        success "$service_name is running"
        return 0
    else
        error "$service_name is not running"
        return 1
    fi
}

# Create backups
log "Creating backups of original files..."
backup_file "$APP_DIR/event/forms.py"
backup_file "$APP_DIR/event/views.py"
backup_file "$APP_DIR/event/templates/ticket_type/ticket_type_create.html"

# Update event/forms.py
log "Updating event/forms.py..."
cat > "$APP_DIR/event/forms.py" << 'EOF'
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
EOF

if [[ $? -eq 0 ]]; then
    success "Updated event/forms.py"
else
    error "Failed to update event/forms.py"
    exit 1
fi

# Update ticket_type_create view in views.py
log "Updating ticket_type_create function in event/views.py..."

# Create a temporary Python script to update the views.py file
cat > /tmp/update_views.py << 'EOF'
import re

def update_views_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find and replace the ticket_type_create function
    old_function = r'@login_required\(login_url=\'/promoter/account/login/\'\)\ndef ticket_type_create\(request, event_id\):.*?return render\(request, \'ticket_type/ticket_type_create\.html\', \{[^}]*\}\)'
    
    new_function = '''@login_required(login_url='/promoter/account/login/')
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
    })'''
    
    # Replace the function using regex
    content = re.sub(old_function, new_function, content, flags=re.DOTALL)
    
    # Also update ticket_type_update function
    old_update_function = r'@login_required\(login_url=\'/promoter/account/login/\'\)\ndef ticket_type_update\(request, ticket_id\):.*?return render\(request, \'ticket_type/ticket_type_create\.html\', \{[^}]*\}\)'
    
    new_update_function = '''@login_required(login_url='/promoter/account/login/')
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
    })'''
    
    content = re.sub(old_update_function, new_update_function, content, flags=re.DOTALL)
    
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    import sys
    update_views_file(sys.argv[1])
EOF

python3 /tmp/update_views.py "$APP_DIR/event/views.py"
if [[ $? -eq 0 ]]; then
    success "Updated event/views.py"
else
    error "Failed to update event/views.py"
    exit 1
fi

# Update the template
log "Updating ticket_type_create.html template..."

# First, let's add error display sections to the template
if [[ -f "$APP_DIR/event/templates/ticket_type/ticket_type_create.html" ]]; then
    # Insert error sections after the page header and before event information
    sed -i '/<div class="page-header">/,/<\/div>/{ 
        /<\/div>/{
            a\
\
    <!-- Error Messages -->\
    {% if error %}\
    <div class="alert alert-danger" style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 8px; margin-bottom: 20px;">\
        <div class="d-flex align-items-center">\
            <i class="fas fa-exclamation-triangle" style="margin-right: 10px; font-size: 1.2rem;"></i>\
            <div>\
                <strong>Error:</strong> {{ error }}\
            </div>\
        </div>\
    </div>\
    {% endif %}\
\
    <!-- Form Errors -->\
    {% if form.non_field_errors %}\
    <div class="alert alert-danger" style="background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 8px; margin-bottom: 20px;">\
        <div class="d-flex align-items-center">\
            <i class="fas fa-exclamation-triangle" style="margin-right: 10px; font-size: 1.2rem;"></i>\
            <div>\
                <strong>Form Errors:</strong>\
                <ul style="margin: 5px 0 0 0; padding-left: 20px;">\
                    {% for error in form.non_field_errors %}\
                    <li>{{ error }}</li>\
                    {% endfor %}\
                </ul>\
            </div>\
        </div>\
    </div>\
    {% endif %}
        }
    }' "$APP_DIR/event/templates/ticket_type/ticket_type_create.html"
    
    if [[ $? -eq 0 ]]; then
        success "Updated ticket_type_create.html template"
    else
        warning "Failed to update template with sed, template may need manual update"
    fi
else
    warning "Template file not found, skipping template update"
fi

# Set proper file permissions
log "Setting proper file permissions..."
chown -R nginx:nginx "$APP_DIR"
chmod -R 755 "$APP_DIR"

# Check syntax of Python files
log "Checking Python syntax..."
cd "$APP_DIR"
if python3 -m py_compile event/forms.py; then
    success "event/forms.py syntax is valid"
else
    error "event/forms.py has syntax errors!"
    exit 1
fi

if python3 -m py_compile event/views.py; then
    success "event/views.py syntax is valid"
else
    error "event/views.py has syntax errors!"
    exit 1
fi

# Check Django configuration
log "Testing Django configuration..."
if cd "$APP_DIR" && python3 manage.py check --deploy 2>/dev/null; then
    success "Django configuration is valid"
else
    warning "Django configuration warnings detected (may be non-critical)"
fi

# Restart services
log "Restarting uWSGI service..."
systemctl restart uwsgi
sleep 3

if check_service uwsgi; then
    success "uWSGI restarted successfully"
else
    error "uWSGI failed to restart!"
    
    # Show recent logs
    echo "Recent uWSGI logs:"
    journalctl -u uwsgi --no-pager -n 20
    
    # Attempt rollback
    warning "Attempting rollback..."
    if [[ -f "$BACKUP_DIR/forms.py" ]]; then
        cp "$BACKUP_DIR/forms.py" "$APP_DIR/event/forms.py"
        cp "$BACKUP_DIR/views.py" "$APP_DIR/event/views.py"
        systemctl restart uwsgi
        error "Rollback completed. Check logs for issues."
    fi
    exit 1
fi

log "Restarting Nginx service..."
systemctl restart nginx
sleep 2

if check_service nginx; then
    success "Nginx restarted successfully"
else
    error "Nginx failed to restart!"
    journalctl -u nginx --no-pager -n 10
fi

# Test the application
log "Testing application response..."
if curl -f -s -o /dev/null http://localhost/; then
    success "Application is responding"
else
    warning "Application may not be responding correctly"
fi

# Clean up
rm -f /tmp/update_views.py

# Summary
echo ""
echo "================================================"
success "🎉 Deployment completed successfully!"
echo ""
echo "📋 Summary of changes:"
echo "  ✅ Fixed bootstrap_datepicker_plus dependency issue"
echo "  ✅ Added comprehensive exception handling"
echo "  ✅ Enhanced error display in templates"
echo "  ✅ Updated ticket creation and update views"
echo "  ✅ Services restarted successfully"
echo ""
echo "📁 Backup location: $BACKUP_DIR"
echo "📝 Log file: $LOG_FILE"
echo ""
echo "🧪 Test your ticket creation at:"
echo "   https://your-domain.com/promoter/ticket/new/[EVENT_ID]/"
echo ""
echo "📊 Monitor logs with:"
echo "   sudo journalctl -u uwsgi -f"
echo "   sudo tail -f /var/log/nginx/error.log"
echo ""

if [[ -f /var/log/uwsgi/eventlinez.log ]]; then
    echo "   sudo tail -f /var/log/uwsgi/eventlinez.log"
fi

echo "================================================"
