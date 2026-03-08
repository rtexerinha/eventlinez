# DOORMAN FUNCTIONALITY GUIDE

## Overview
The doorman feature allows event organizers to assign staff members who can check-in attendees without seeing financial information (ticket prices, revenue, etc.).

## Features Implemented

### 1. **Doorman Role**
- Doormen can only see:
  - Event name, date, and location
  - Ticket holder names
  - Check-in status
  - Total ticket counts (NO PRICES)

### 2. **Web Interface**
- **Dashboard**: `/promoter/doorman/` - Shows assigned events
- **Check-In Page**: `/promoter/doorman/event/<event_id>/checkin/` - View and search tickets

### 3. **API Endpoints** (Already existed)
- QR code scanning
- Real-time check-in stats
- Ticket validation

## How to Assign a Doorman (Admin/Promoter Only)

### Method 1: Via Django Admin Panel

1. Go to: `http://localhost:8000/admin/`
2. Navigate to **Promoter > Partners**
3. Click **Add Partner**
4. Fill in:
   - **Email**: The user's registered email
   - **User**: Select the user from dropdown
   - **Role**: Choose "DOORMAN"
   - **Event**: Select the event
   - **Disable**: Leave unchecked
5. Click **Save**

### Method 2: Via API (Recommended)

**Endpoint**: `POST /promoter/api/doorman/assign/`

**Headers**:
```
Authorization: Token <promoter-token>
Content-Type: application/json
```

**Body**:
```json
{
  "email": "doorman@example.com",
  "event_id": 5
}
```

**Response**:
```json
{
  "message": "doorman@example.com has been assigned as a Doorman for 'Event Name'.",
  "partner_id": 123,
  "created": true
}
```

### Method 3: List Existing Doormen

**Endpoint**: `GET /promoter/api/doorman/list/?event_id=5`

**Response**:
```json
[
  {
    "partner_id": 123,
    "email": "doorman@example.com",
    "name": "John Doe",
    "event_id": 5,
    "event_name": "Summer Festival",
    "active": true,
    "assigned_at": "2026-03-06T10:00:00Z"
  }
]
```

## User Registration Required

⚠️ **IMPORTANT**: The doorman user MUST register an account first:
1. Go to: `http://localhost:8000/promoter/account/create/`
2. Register with email/password
3. Then the admin can assign them to events

## Doorman Access

### Web Access
1. Doorman logs in: `http://localhost:8000/promoter/account/login/`
2. Automatically redirected to: `http://localhost:8000/promoter/doorman/`
3. Can see assigned events and start check-in

### Mobile App Access
- Use existing API endpoints for QR code scanning
- All doorman APIs work with both web and mobile

## What Doormen CAN See
✅ Event name, date, location
✅ Ticket holder names
✅ Check-in status and timestamps
✅ Total ticket counts
✅ Guest list / complimentary tickets

## What Doormen CANNOT See
❌ Ticket prices
❌ Revenue/sales data
❌ Payment information
❌ Financial reports
❌ Vendor commissions
❌ Promo code discounts

## Remove/Disable a Doorman

**Endpoint**: `DELETE /promoter/api/doorman/assign/<partner_id>/`

**Response**:
```json
{
  "message": "Doorman doorman@example.com has been disabled for 'Event Name'."
}
```

## Check-In Process

### Web Interface
1. Doorman opens event check-in page
2. Search by name, email, or ticket ID
3. View check-in status (manual verification)

### Mobile App (QR Scanning)
1. Use API endpoint: `POST /promoter/api/doorman/scan/ticket/`
2. Body: `{"uuid": "<ticket-uuid>", "event_id": <id>}`
3. Returns success/failure and updates check-in status

## Security
- Doormen are restricted by the `IsDoorman` permission class
- Can only access assigned events
- Cannot modify event settings or see financial data
- All actions are logged

## Troubleshooting

### "You don't have doorman access"
- User is not assigned as doorman to any event
- Check Partner table in admin

### "Event not found"
- Doorman not assigned to this specific event
- Admin needs to create Partner record

### "User with email X not found"
- User must register first before being assigned as doorman
- Send them the registration link

## Example Workflow

1. **Promoter creates event**
2. **User registers**: `doorman@example.com`
3. **Promoter assigns via API**:
   ```bash
   curl -X POST http://localhost:8000/promoter/api/doorman/assign/ \
     -H "Authorization: Token <token>" \
     -H "Content-Type: application/json" \
     -d '{"email":"doorman@example.com","event_id":5}'
   ```
4. **Doorman logs in** and sees event on dashboard
5. **Doorman performs check-ins** on event day

---

**Note**: The Partner model already existed in your codebase with DOORMAN role support. I've added the web interface views and templates to complement the existing API functionality.
