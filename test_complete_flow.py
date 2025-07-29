#!/usr/bin/env python3
import requests
import json

def test_complete_auth_flow():
    """Test the complete authentication flow with proper password"""
    
    # Test data with strong password (matching frontend format)
    test_data = {
        "firstName": "Jane",
        "lastName": "Smith", 
        "email": "jane.smith2@example.com",  # Use different email to avoid conflicts
        "phone": "1234567890",
        "password": "MyStr0ngP@ssw0rd123!",
        "confirmPassword": "MyStr0ngP@ssw0rd123!"
    }
    
    print("=== Testing Complete Auth Flow ===")
    
    # Step 1: Register
    print("\n1. Testing Registration...")
    register_url = "http://localhost:8000/api/auth/register/"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(register_url, json=test_data, headers=headers)
        print(f"Register Status: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            register_data = response.json()
            print(f"User ID: {register_data['user']['id']}")
            print(f"Email: {register_data['user']['email']}")
            print(f"Verified: {register_data['user']['isVerified']}")
        else:
            print("❌ Registration failed!")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False
    
    # Step 2: Try login before verification (should fail)
    print("\n2. Testing Login Before Verification...")
    login_data = {
        "email": test_data["email"],
        "password": test_data["password"]
    }
    
    login_url = "http://localhost:8000/api/auth/login/"
    
    try:
        response = requests.post(login_url, json=login_data, headers=headers)
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 400:
            error_data = response.json()
            print("✅ Login correctly blocked before verification!")
            print(f"Error message: {error_data.get('non_field_errors', ['Unknown error'])[0]}")
        else:
            print("❌ Login should have failed before verification!")
            return False
            
    except Exception as e:
        print(f"❌ Login test error: {e}")
        return False
    
    # Step 3: Verify OTP (using bypass)
    print("\n3. Testing OTP Verification...")
    otp_data = {
        "email": test_data["email"],
        "otp": "123456"  # Any 6-digit code works due to bypass
    }
    
    otp_url = "http://localhost:8000/api/auth/verify-otp/"
    
    try:
        response = requests.post(otp_url, json=otp_data, headers=headers)
        print(f"OTP Verification Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ OTP verification successful!")
            otp_response = response.json()
            print(f"User verified: {otp_response['user']['isVerified']}")
            print(f"Access token received: {'access' in otp_response['tokens']}")
            access_token = otp_response['tokens']['access']
        else:
            print("❌ OTP verification failed!")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OTP verification error: {e}")
        return False
    
    # Step 4: Login after verification (should succeed)
    print("\n4. Testing Login After Verification...")
    
    try:
        response = requests.post(login_url, json=login_data, headers=headers)
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login successful after verification!")
            login_response = response.json()
            print(f"User: {login_response['user']['firstName']} {login_response['user']['lastName']}")
            print(f"Access token received: {'access' in login_response['tokens']}")
        else:
            print("❌ Login failed after verification!")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login after verification error: {e}")
        return False
    
    # Step 5: Test authenticated endpoint
    print("\n5. Testing Authenticated Endpoint...")
    profile_url = "http://localhost:8000/api/auth/profile/"
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(profile_url, headers=auth_headers)
        print(f"Profile Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Authenticated request successful!")
            profile_data = response.json()
            print(f"Profile: {profile_data['firstName']} {profile_data['lastName']}")
        else:
            print("❌ Authenticated request failed!")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Profile request error: {e}")
        return False
    
    print("\n🎉 All tests passed! Authentication flow is working correctly.")
    return True

def test_weak_password():
    """Test that weak passwords are properly rejected"""
    print("\n=== Testing Weak Password Rejection ===")
    
    weak_password_data = {
        "firstName": "Test",
        "lastName": "User", 
        "email": "test.weak@example.com",
        "phone": "1234567890",
        "password": "password123",  # Weak password
        "confirmPassword": "password123"
    }
    
    register_url = "http://localhost:8000/api/auth/register/"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(register_url, json=weak_password_data, headers=headers)
        print(f"Weak Password Test Status: {response.status_code}")
        
        if response.status_code == 400:
            error_data = response.json()
            print("✅ Weak password correctly rejected!")
            print(f"Error: {error_data.get('password', ['Unknown error'])[0]}")
            return True
        else:
            print("❌ Weak password should have been rejected!")
            return False
            
    except Exception as e:
        print(f"❌ Weak password test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Authentication System Tests...")
    
    # Test complete flow
    flow_success = test_complete_auth_flow()
    
    # Test weak password rejection
    weak_password_success = test_weak_password()
    
    if flow_success and weak_password_success:
        print("\n✅ All authentication tests passed!")
        print("The 400 errors you were seeing are actually correct behavior:")
        print("- Registration rejects weak passwords (Django security)")
        print("- Login blocks unverified users (email verification required)")
        print("- Frontend should now show proper error messages")
    else:
        print("\n❌ Some tests failed. Check the output above.")