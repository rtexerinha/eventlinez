# Abandoned Cart Tracking & Reminder System

This system automatically tracks customers who add tickets to their cart but don't complete the purchase, and sends reminder emails after 30 minutes.

## Features

### ✅ **Completed Implementation**

1. **Automatic Cart Tracking**
   - Tracks when customers view their cart with items
   - Records customer email, cart contents, and abandonment time
   - Stores detailed cart item information for emails

2. **Admin Interface**
   - View all abandoned carts in Django Admin
   - Filter by status, date, email
   - Send reminder emails manually
   - Mark carts as converted or expired
   - Detailed cart information and timeline

3. **Automated Reminder System**
   - Management command to send reminder emails
   - Beautiful HTML and text email templates
   - Tracks reminder status and counts
   - Automatic cart expiry after 24 hours

4. **Template Fixes**
   - Fixed Django template syntax errors in cart.html
   - Improved cart display and error handling

## How to Use

### **Admin Interface**

1. **Access Abandoned Carts**:
   - Go to Django Admin: `http://localhost:8000/admin/`
   - Navigate to: `Cart > Abandoned Carts`

2. **View Cart Details**:
   - See customer info, cart value, items
   - Check time since abandonment
   - View reminder status

3. **Manual Actions**:
   - Select carts and use "Send reminder emails" action
   - Mark carts as expired or converted
   - View detailed cart items inline

### **Automated Reminders**

1. **Test the System**:
   ```bash
   # Dry run to see what would be sent
   python manage.py send_cart_reminders --dry-run
   
   # Actually send emails
   python manage.py send_cart_reminders
   ```

2. **Schedule with Cron** (Production):
   ```bash
   # Add to crontab to run every 30 minutes
   */30 * * * * cd /path/to/eventlinez && python manage.py send_cart_reminders
   ```

### **How Cart Tracking Works**

1. **Customer adds tickets to cart**
2. **Customer views cart page** → System tracks abandonment
3. **After 30 minutes** → Cart becomes eligible for reminder
4. **Admin/Cron sends reminder** → Email sent, status updated
5. **After 24 hours** → Cart marked as expired
6. **If customer completes purchase** → Cart marked as converted

## Email Templates

### **Locations**:
- HTML: `cart/templates/cart/emails/cart_reminder.html`
- Text: `cart/templates/cart/emails/cart_reminder.txt`

### **Customization**:
- Modify templates to match your brand
- Update email subject in management command
- Add more email templates for different timing

## Database Models

### **AbandonedCart**
- Tracks cart abandonment details
- Links to original Cart and User
- Stores customer email and cart totals
- Tracks reminder status and timing

### **AbandonedCartItem**
- Detailed items in abandoned cart
- Stores ticket names, event details
- Used for email content generation

## Configuration

### **Required Settings**:
```python
# In settings.py
EMAIL_HOST = 'your-smtp-server.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'your-email@domain.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'noreply@eventlinez.com'
APP_HOST = 'https://your-domain.com'  # For cart URLs in emails
```

### **Optional Settings**:
```python
# Customize timing
CART_ABANDONMENT_THRESHOLD = 30  # minutes
CART_EXPIRY_THRESHOLD = 24  # hours
```

## Testing

### **Create Test Abandoned Cart**:
1. Add tickets to cart while logged in
2. Visit cart page (this triggers tracking)
3. Wait or manually adjust timestamps in admin
4. Run reminder command

### **Check Email Delivery**:
1. Use `--dry-run` first to test without sending
2. Check Django logs for email errors
3. Verify SMTP settings are correct

## Admin Features

### **List View**:
- Cart ID, customer info, total amount
- Status indicators (color-coded)
- Time since abandonment
- Quick action links

### **Detail View**:
- Complete cart information
- Inline cart items
- Reminder history
- Conversion tracking

### **Bulk Actions**:
- Send reminders to multiple carts
- Mark multiple carts as expired
- Export cart data

## Monitoring

### **Key Metrics to Track**:
- Abandonment rate
- Reminder email open rates
- Conversion rate after reminders
- Revenue recovered from abandoned carts

### **Admin Reports**:
- Filter by date ranges
- Group by reminder status
- Calculate total abandoned value

## Troubleshooting

### **Common Issues**:
1. **No emails being sent**: Check SMTP settings
2. **Carts not being tracked**: Ensure users are logged in
3. **Wrong timing**: Check server timezone settings
4. **Template errors**: Verify template paths exist

### **Debug Commands**:
```bash
# Check for eligible carts
python manage.py shell -c "from cart.utils import get_eligible_carts_for_reminder; print(get_eligible_carts_for_reminder().count())"

# Test email settings
python manage.py shell -c "from django.core.mail import send_mail; send_mail('Test', 'Test message', 'from@domain.com', ['to@domain.com'])"
```

## Next Steps

### **Recommended Enhancements**:
1. A/B test different email templates
2. Add multiple reminder emails (1 hour, 24 hours)
3. SMS reminders for high-value carts
4. Discount codes in reminder emails
5. Web push notifications
6. Analytics dashboard for abandonment metrics

The system is now fully functional and ready for production use!
