from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# 1. Register a new user
print('=== REGISTER ===')
res = client.post('/api/v1/auth/register', json={
    'email': 'testlogin@example.com',
    'password': 'Password123!',
    'full_name': 'Test Login User',
    'business_name': 'Test Business',
    'business_type': 'plumber',
    'postcode': 'SW1A 1AA'
})
print('Status:', res.status_code)
print('Has access_token:', 'access_token' in res.json())
token = res.json().get('access_token')

# 2. Login with the same credentials
print('\n=== LOGIN ===')
res = client.post('/api/v1/auth/login', json={
    'email': 'testlogin@example.com',
    'password': 'Password123!'
})
print('Status:', res.status_code)
data = res.json()
print('Response keys:', list(data.keys()))
print('requires_2fa:', data.get('requires_2fa'))
print('Has access_token:', 'access_token' in data)
access_token = data['access_token']

# 3. Access /me with token
print('\n=== ME ===')
res = client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer ' + access_token})
print('Status:', res.status_code)
print('User:', res.json().get('email'))

# 4. Test wrong password
print('\n=== WRONG PASSWORD ===')
res = client.post('/api/v1/auth/login', json={
    'email': 'testlogin@example.com',
    'password': 'WrongPassword123!'
})
print('Status:', res.status_code)
print('Detail:', res.json().get('detail'))
