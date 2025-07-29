#!/usr/bin/env python3
import requests
import json

def test_password_mismatch():
    """Test that password mismatch is properly handled"""
    print("=== Testing Password Mismatch ===")
    
    # Test data with mismatched passwords
    test_data = {
        "firstName": "Test",
        "lastName": "User", 
        "email": "test.mismatch@example.com",
        "phone": "1234567890",
        "password": "MyStr0ngP@ssw0rd123!",
        "confirmPassword": "DifferentP@ssw0rd123!"  # Different password
    }
    
    register_url = "http://localhost:8000/api/auth/register/"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(register_url, json=test_data, headers=headers)
        print(f"Password Mismatch Test Status: {response.status_code}")
        
        if response.status_code == 400:
            error_data = response.json()
            print("✅ Password mismatch correctly detected!")
            print(f"Error: {error_data}")
            return True
        else:
            print("❌ Password mismatch should have been detected!")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Password mismatch test error: {e}")
        return False

def test_missing_confirmpassword():
    """Test that missing confirmPassword is properly handled"""
    print("\n=== Testing Missing confirmPassword ===")
    
    # Test data without confirmPassword
    test_data = {
        "firstName": "Test",
        "lastName": "User", 
        "email": "test.missing@example.com",
        "phone": "1234567890",
        "password": "MyStr0ngP@ssw0rd123!"
        # Missing confirmPassword field
    }
    
    register_url = "http://localhost:8000/api/auth/register/"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(register_url, json=test_data, headers=headers)
        print(f"Missing confirmPassword Test Status: {response.status_code}")
        
        if response.status_code == 400:
            error_data = response.json()
            print("✅ Missing confirmPassword correctly detected!")
            print(f"Error: {error_data}")
            return True
        else:
            print("❌ Missing confirmPassword should have been detected!")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Missing confirmPassword test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Password Validation...")
    
    mismatch_success = test_password_mismatch()
    missing_success = test_missing_confirmpassword()
    
    if mismatch_success and missing_success:
        print("\n✅ All password validation tests passed!")
        print("The confirmPassword field is now working correctly.")
    else:
        print("\n❌ Some password validation tests failed.")