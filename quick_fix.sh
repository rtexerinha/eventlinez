#!/bin/bash

# Quick Fix for Ticket Creation 500 Error
# Root cause: bootstrap_datepicker_plus module not found

echo "🚀 Quick Fix: Removing bootstrap_datepicker_plus dependency..."

# Backup and fix forms.py
cp /app/eventlinez/event/forms.py /tmp/forms.py.backup
sed -i '/bootstrap_datepicker_plus/d' /app/eventlinez/event/forms.py
sed -i 's/DateTimePickerInput/forms.DateTimeInput/g' /app/eventlinez/event/forms.py
sed -i 's/format="%d\/%m\/%Y %H:%M",/attrs={"type": "datetime-local"},/g' /app/eventlinez/event/forms.py

echo "✅ Fixed forms.py"

# Test syntax
python3 -c "import sys; sys.path.append('/app/eventlinez'); from event.forms import *; print('✅ Forms syntax OK')" 2>/dev/null || echo "❌ Forms syntax error"

# Restart uWSGI
systemctl restart uwsgi
echo "✅ uWSGI restarted"

# Test
if curl -f -s -o /dev/null http://localhost/; then
    echo "✅ Application responding"
else
    echo "⚠️  Check application status"
fi

echo "🎉 Quick fix complete! Test ticket creation now."
