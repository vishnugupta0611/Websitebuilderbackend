#!/usr/bin/env python3
import requests
import json

# Test data
test_data = {
    "firstName": "John",
    "lastName": "Doe", 
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "password": "testpass123",
    "confirmPassword": "testpass123"
}

# Make request
url = "http://localhost:8000/api/auth/register/"
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=test_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 400:
        try:
            error_data = response.json()
            print(f"Error Details: {json.dumps(error_data, indent=2)}")
        except:
            print("Could not parse error response as JSON")
            
except requests.exceptions.ConnectionError:
    print("Could not connect to the server. Make sure Django is running on localhost:8000")
except Exception as e:
    print(f"Error: {e}")