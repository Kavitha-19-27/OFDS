import requests

url = "http://localhost:8001/api/v1/auth/register"
data = {
    "email": "Dinesh@gmail.com",
    "password": "Test@123456",
    "full_name": "Dinesh",
    "tenant_name": "TestOrg"
}

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
