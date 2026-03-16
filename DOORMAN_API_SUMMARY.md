# Doorman API Implementation Summary

## ✅ New Endpoints Created

### 1. Doorman Ticket Search (Manual Check-In)
**Endpoint:** `GET /promoter/api/doorman/ticket-search/`

**Query Parameters:**
- `event_id` (required): Event ID to search within
- `guest_name` (optional): Search by guest name
- `guest_email` (optional): Search by guest email

**Response Example:**
```json
[
  {
    "id": 123,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "guest_name": "John Doe",
    "guest_email": "john@example.com",
    "event_ticket": {
      "name": "General Admission",
      "price": 50.0
    },
    "checkin_date": null,
    "created_at": "2026-03-15T10:00:00Z",
    "is_checked_in": false
  }
]
```

### 2. Doorman Guest List (Read-Only)
**Endpoint:** `GET /promoter/api/doorman/guest-list/?event_id={id}`

**Query Parameters:**
- `event_id` (required): Event ID
- `search` (optional): Search by name or email
- `status` (optional): PENDING, SENT, CHECKED_IN, CANCELLED

**Response Example:**
```json
{
  "guests": [...],
  "stats": {
    "total": 50,
    "pending": 10,
    "sent": 30,
    "checked_in": 5,
    "cancelled": 5
  },
  "event_name": "Summer Festival 2026",
  "event_date": "2026-07-15T18:00:00Z"
}
```

## ✅ QR Code Compatibility Verified

Both paid tickets and guest list tickets **work with the same QR scanner**:

- **Paid Tickets:** `/promoter/api/doorman/scan/ticket/` (POST with uuid)
- **Guest List:** `/promoter/api/doorman/scan/guest/` (POST with uuid)
- Both use UUID-based QR codes
- Same permission system (IsDoorman)
- Can be scanned at the same entrance

## Mobile App Integration

Update your app to use doorman-specific endpoints when `isDoorman === true`:

```typescript
// Ticket Search
const searchUrl = isDoorman 
  ? `/promoter/api/doorman/ticket-search/?event_id=${eventId}&guest_name=${name}`
  : `/ticket/api/search?event_id=${eventId}&guest_name=${name}`;

// Guest List View
const guestListUrl = `/promoter/api/doorman/guest-list/?event_id=${eventId}`;
```

QR scanning endpoints remain unchanged - they already work for both doormen and promoters.

## Security

- All endpoints require authentication
- IsDoorman permission (allows both promoters + assigned doormen)
- Event access verified per request
- Doormen can only access assigned events
