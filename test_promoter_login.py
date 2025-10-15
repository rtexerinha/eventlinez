import requests
import sys

# Start a session
session = requests.Session()

# First, get the login page to get CSRF token
login_url = 'http://localhost:8000/promoter/account/login/'
response = session.get(login_url)

if response.status_code != 200:
    print(f"Failed to get login page: {response.status_code}")
    sys.exit(1)

# Extract CSRF token
from bs4 import BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})

if not csrf_token:
    print("Could not find CSRF token")
    sys.exit(1)

csrf_value = csrf_token.get('value')
print(f"Found CSRF token: {csrf_value}")

# Login with credentials
login_data = {
    'username': 'calisamba@gmail.com',
    'password': '123456',
    'csrfmiddlewaretoken': csrf_value
}

login_response = session.post(login_url, data=login_data)
print(f"Login response status: {login_response.status_code}")
print(f"Login response URL: {login_response.url}")

# Now try to access the promoter events page
events_url = 'http://localhost:8000/promoter/events/'
events_response = session.get(events_url)

print(f"Events page status: {events_response.status_code}")
print(f"Events page URL: {events_response.url}")

if events_response.status_code == 500:
    print("=== 500 ERROR CONTENT ===")
    print(events_response.text[:2000])  # First 2000 chars
else:
    print("=== RESPONSE CONTENT (first 500 chars) ===")
    print(events_response.text[:500])
