import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventlinez.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from promoter.models import PromoCode, PromoCodeUsage
from event.models import Event

results = []

def check(label, condition, got=None):
    status = "PASS" if condition else "FAIL"
    msg = f"[{status}] {label}" + (f" (got: {got})" if got is not None else "")
    results.append(msg)
    print(msg)

user = User.objects.get(username='calisamba@gmail.com')
promoter = user.promoter
event = Event.objects.filter(promoter=promoter).first()
token, _ = Token.objects.get_or_create(user=user)
client = APIClient()
client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
anon = APIClient()
now = timezone.now()

print(f"Promoter: {user.username} | Event: {event.name} (id={event.id})\n")

# 1. LIST
r = client.get('/promoter/api/promo-codes/')
check("1. LIST 200", r.status_code == 200, r.status_code)

# 2. CREATE valid percentage code
r = client.post('/promoter/api/promo-codes/', {
    "code": "AUDIT10", "event": event.id,
    "discount_type": "percentage", "discount_value": "10.00",
    "max_uses": 5, "max_uses_per_customer": 2,
    "valid_from": (now - timedelta(days=1)).isoformat(),
    "valid_until": (now + timedelta(days=30)).isoformat(),
}, format='json')
check("2. CREATE 201", r.status_code == 201, r.status_code)
check("2. code=AUDIT10", r.data.get('code') == 'AUDIT10', r.data.get('code'))
check("2. current_uses=0", r.data.get('current_uses') == 0, r.data.get('current_uses'))
check("2. uses_remaining=5", r.data.get('uses_remaining') == 5, r.data.get('uses_remaining'))
check("2. is_valid=True", r.data.get('is_valid') is True, r.data.get('is_valid'))
check("2. usages list present", isinstance(r.data.get('usages'), list), type(r.data.get('usages')).__name__)
promo_id = r.data.get('id')

# 3. DETAIL
r = client.get(f'/promoter/api/promo-codes/{promo_id}/')
check("3. DETAIL 200", r.status_code == 200, r.status_code)

# 4. VALIDATE percentage
r = anon.post('/promoter/api/promo-codes/validate/', {"code": "AUDIT10", "event_id": event.id, "subtotal": "100.00"}, format='json')
check("4. VALIDATE 200", r.status_code == 200, r.status_code)
check("4. valid=True", r.data.get('valid') is True, r.data.get('valid'))
check("4. discount_amount=10.00", r.data.get('discount_amount') == '10.00', r.data.get('discount_amount'))
check("4. new_total=90.00", r.data.get('new_total') == '90.00', r.data.get('new_total'))

# 5. VALIDATE amount discount
PromoCode.objects.filter(id=promo_id).update(discount_type='amount', discount_value='7.50')
r = anon.post('/promoter/api/promo-codes/validate/', {"code": "AUDIT10", "event_id": event.id, "subtotal": "100.00"}, format='json')
check("5. VALIDATE amount discount=7.50", r.data.get('discount_amount') == '7.50', r.data.get('discount_amount'))
check("5. VALIDATE amount new_total=92.50", r.data.get('new_total') == '92.50', r.data.get('new_total'))
PromoCode.objects.filter(id=promo_id).update(discount_type='percentage', discount_value='10.00')

# 6. VALIDATE amount larger than subtotal (should clamp to subtotal)
PromoCode.objects.filter(id=promo_id).update(discount_type='amount', discount_value='200.00')
r = anon.post('/promoter/api/promo-codes/validate/', {"code": "AUDIT10", "event_id": event.id, "subtotal": "50.00"}, format='json')
check("6. VALIDATE amount > subtotal: new_total=0.00", r.data.get('new_total') == '0.00', r.data.get('new_total'))
PromoCode.objects.filter(id=promo_id).update(discount_type='percentage', discount_value='10.00')

# 7. VALIDATE wrong event
r = anon.post('/promoter/api/promo-codes/validate/', {"code": "AUDIT10", "event_id": 99999, "subtotal": "100.00"}, format='json')
check("7. VALIDATE wrong event 404", r.status_code == 404, r.status_code)
check("7. VALIDATE wrong event valid=False", r.data.get('valid') is False, r.data.get('valid'))

# 8. VALIDATE exhausted
PromoCode.objects.filter(id=promo_id).update(current_uses=5, max_uses=5)
r = anon.post('/promoter/api/promo-codes/validate/', {"code": "AUDIT10", "event_id": event.id, "subtotal": "100.00"}, format='json')
check("8. VALIDATE exhausted valid=False", r.data.get('valid') is False, r.data.get('valid'))
check("8. VALIDATE exhausted has error msg", bool(r.data.get('error')), r.data.get('error'))
PromoCode.objects.filter(id=promo_id).update(current_uses=0, max_uses=5)

# 9. VALIDATE inactive
PromoCode.objects.filter(id=promo_id).update(is_active=False)
r = anon.post('/promoter/api/promo-codes/validate/', {"code": "AUDIT10", "event_id": event.id, "subtotal": "100.00"}, format='json')
check("9. VALIDATE inactive valid=False", r.data.get('valid') is False, r.data.get('valid'))
PromoCode.objects.filter(id=promo_id).update(is_active=True)

# 10. VALIDATE expired
PromoCode.objects.filter(id=promo_id).update(valid_until=now - timedelta(days=1))
r = anon.post('/promoter/api/promo-codes/validate/', {"code": "AUDIT10", "event_id": event.id, "subtotal": "100.00"}, format='json')
check("10. VALIDATE expired valid=False", r.data.get('valid') is False, r.data.get('valid'))
PromoCode.objects.filter(id=promo_id).update(valid_until=now + timedelta(days=30))

# 11. PATCH
r = client.patch(f'/promoter/api/promo-codes/{promo_id}/', {"max_uses": 20}, format='json')
check("11. PATCH 200", r.status_code == 200, r.status_code)
check("11. PATCH max_uses=20", r.data.get('max_uses') == 20, r.data.get('max_uses'))
check("11. PATCH uses_remaining=20", r.data.get('uses_remaining') == 20, r.data.get('uses_remaining'))

# 12. PATCH event is immutable
other_event = Event.objects.exclude(id=event.id).first()
if other_event:
    r = client.patch(f'/promoter/api/promo-codes/{promo_id}/', {"event": other_event.id}, format='json')
    check("12. PATCH event ignored (immutable)", r.data.get('event') == event.id, r.data.get('event'))

# 13. TOGGLE
r = client.post(f'/promoter/api/promo-codes/{promo_id}/toggle/')
check("13. TOGGLE 200", r.status_code == 200, r.status_code)
check("13. TOGGLE is_active=False", r.data.get('is_active') is False, r.data.get('is_active'))
r = client.post(f'/promoter/api/promo-codes/{promo_id}/toggle/')
check("13. TOGGLE back is_active=True", r.data.get('is_active') is True, r.data.get('is_active'))

# 14. SECURITY: wrong promoter cannot read/edit/delete
other_user = User.objects.exclude(id=user.id).filter(promoter__isnull=False).first()
if other_user:
    ot, _ = Token.objects.get_or_create(user=other_user)
    other = APIClient()
    other.credentials(HTTP_AUTHORIZATION=f'Token {ot.key}')
    check("14. SECURITY GET wrong promoter=404", other.get(f'/promoter/api/promo-codes/{promo_id}/').status_code == 404)
    check("14. SECURITY PATCH wrong promoter=404", other.patch(f'/promoter/api/promo-codes/{promo_id}/', {"max_uses": 999}, format='json').status_code == 404)
    check("14. SECURITY DELETE wrong promoter=404", other.delete(f'/promoter/api/promo-codes/{promo_id}/').status_code == 404)

# 15. CREATE duplicate code rejected
r = client.post('/promoter/api/promo-codes/', {
    "code": "AUDIT10", "event": event.id,
    "discount_type": "percentage", "discount_value": "10.00",
    "max_uses": 1, "max_uses_per_customer": 1,
    "valid_from": (now - timedelta(days=1)).isoformat(),
    "valid_until": (now + timedelta(days=30)).isoformat(),
}, format='json')
check("15. CREATE duplicate code=400", r.status_code == 400, r.status_code)

# 16. CREATE percentage > 100 rejected
r = client.post('/promoter/api/promo-codes/', {
    "code": "BAD999", "event": event.id,
    "discount_type": "percentage", "discount_value": "150.00",
    "max_uses": 1, "max_uses_per_customer": 1,
    "valid_from": (now - timedelta(days=1)).isoformat(),
    "valid_until": (now + timedelta(days=30)).isoformat(),
}, format='json')
check("16. CREATE pct>100 = 400", r.status_code == 400, r.status_code)

# 17. CREATE valid_until before valid_from rejected
r = client.post('/promoter/api/promo-codes/', {
    "code": "BADDATES", "event": event.id,
    "discount_type": "percentage", "discount_value": "10.00",
    "max_uses": 1, "max_uses_per_customer": 1,
    "valid_from": (now + timedelta(days=5)).isoformat(),
    "valid_until": (now + timedelta(days=1)).isoformat(),
}, format='json')
check("17. CREATE valid_until<valid_from = 400", r.status_code == 400, r.status_code)

# 18. VALIDATE missing required fields
r = anon.post('/promoter/api/promo-codes/validate/', {"code": "AUDIT10"}, format='json')
check("18. VALIDATE missing fields = 400", r.status_code == 400, r.status_code)

# 19. LIST filtered by event_id
r = client.get(f'/promoter/api/promo-codes/?event_id={event.id}')
check("19. LIST ?event_id filter 200", r.status_code == 200, r.status_code)
check("19. LIST contains AUDIT10", any(p['code'] == 'AUDIT10' for p in r.data))

# 20. Unauthenticated access to protected endpoints
check("20. LIST no auth=401/403", anon.get('/promoter/api/promo-codes/').status_code in (401, 403))
check("20. CREATE no auth=401/403", anon.post('/promoter/api/promo-codes/', {}, format='json').status_code in (401, 403))
check("20. DETAIL no auth=401/403", anon.get(f'/promoter/api/promo-codes/{promo_id}/').status_code in (401, 403))
check("20. PATCH no auth=401/403", anon.patch(f'/promoter/api/promo-codes/{promo_id}/', {}, format='json').status_code in (401, 403))
check("20. DELETE no auth=401/403", anon.delete(f'/promoter/api/promo-codes/{promo_id}/').status_code in (401, 403))

# 21. DELETE
r = client.delete(f'/promoter/api/promo-codes/{promo_id}/')
check("21. DELETE 204", r.status_code == 204, r.status_code)
check("21. GET after DELETE=404", client.get(f'/promoter/api/promo-codes/{promo_id}/').status_code == 404)
r = anon.post('/promoter/api/promo-codes/validate/', {"code": "AUDIT10", "event_id": event.id, "subtotal": "100.00"}, format='json')
check("21. VALIDATE deleted code=404", r.status_code == 404, r.status_code)

# Summary
passed = sum(1 for r in results if r.startswith('[PASS]'))
failed = sum(1 for r in results if r.startswith('[FAIL]'))
print(f"\n{'='*50}")
print(f"RESULTS: {passed} passed, {failed} failed out of {len(results)} checks")
if failed:
    print("\nFAILED CHECKS:")
    for r in results:
        if r.startswith('[FAIL]'):
            print(f"  {r}")
