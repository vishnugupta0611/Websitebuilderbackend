#!/usr/bin/env python3
import requests
import json

def test_website_data():
    """Test website data structure and hero image"""
    
    print("=== Testing Website Data Structure ===")
    
    # First, let's register and login to get a token
    test_data = {
        "firstName": "Test",
        "lastName": "User", 
        "email": "test.website@example.com",
        "phone": "1234567890",
        "password": "MyStr0ngP@ssw0rd123!",
        "confirmPassword": "MyStr0ngP@ssw0rd123!"
    }
    
    headers = {"Content-Type": "application/json"}
    
    # Register
    print("\n1. Registering user...")
    register_url = "http://localhost:8000/api/auth/register/"
    response = requests.post(register_url, json=test_data, headers=headers)
    
    if response.status_code != 201:
        print("Registration failed, trying to login with existing user...")
    
    # Verify OTP
    print("\n2. Verifying OTP...")
    otp_data = {
        "email": test_data["email"],
        "otp": "123456"
    }
    otp_url = "http://localhost:8000/api/auth/verify-otp/"
    response = requests.post(otp_url, json=otp_data, headers=headers)
    
    if response.status_code != 200:
        print("OTP verification failed, trying to login...")
    
    # Login
    print("\n3. Logging in...")
    login_data = {
        "email": test_data["email"],
        "password": test_data["password"]
    }
    login_url = "http://localhost:8000/api/auth/login/"
    response = requests.post(login_url, json=login_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return False
    
    login_response = response.json()
    access_token = login_response['tokens']['access']
    
    # Create a test website
    print("\n4. Creating test website...")
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    website_data = {
        "name": "Test Website",
        "slug": "test-website-hero",
        "description": "A test website for hero image testing",
        "category": "business",
        "template_id": "hero-products",
        "template_name": "Hero Products Template",
        "heroTitle": "Welcome to Our Amazing Website",
        "heroDescription": "This is a test description for our hero section",
        "heroImage": "https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80",
        "heroButtonText": "Get Started Now",
        "productSectionTitle": "Featured Products",
        "blogSectionTitle": "Latest News",
        "customizations": {
            "colors": {
                "primary": "#3B82F6",
                "secondary": "#6B7280",
                "accent": "#F59E0B",
                "background": "#FFFFFF",
                "text": "#1F2937"
            },
            "typography": {
                "headingFont": "Inter, sans-serif",
                "bodyFont": "Inter, sans-serif"
            }
        },
        "status": "published"
    }
    
    create_url = "http://localhost:8000/api/websites/"
    response = requests.post(create_url, json=website_data, headers=auth_headers)
    
    if response.status_code == 201:
        print("✅ Website created successfully!")
        created_website = response.json()
        website_id = created_website['id']
        print(f"Website ID: {website_id}")
        print(f"Website Slug: {created_website['slug']}")
        print(f"Hero Image: {created_website.get('heroImage', 'NOT SET')}")
    else:
        print(f"❌ Website creation failed: {response.text}")
        return False
    
    # Test getting website by slug (public endpoint)
    print("\n5. Testing public website retrieval...")
    public_url = f"http://localhost:8000/api/websites/by_slug/?slug=test-website-hero"
    response = requests.get(public_url)
    
    if response.status_code == 200:
        print("✅ Website retrieved successfully!")
        website_data = response.json()
        
        print("\n=== WEBSITE DATA STRUCTURE ===")
        print(f"ID: {website_data.get('id')}")
        print(f"Name: {website_data.get('name')}")
        print(f"Slug: {website_data.get('slug')}")
        print(f"Description: {website_data.get('description')}")
        print(f"Template ID: {website_data.get('template_id')}")
        print(f"Template Name: {website_data.get('template_name')}")
        print(f"Hero Title: {website_data.get('heroTitle')}")
        print(f"Hero Description: {website_data.get('heroDescription')}")
        print(f"Hero Image: {website_data.get('heroImage')}")
        print(f"Hero Button Text: {website_data.get('heroButtonText')}")
        print(f"Product Section Title: {website_data.get('productSectionTitle')}")
        print(f"Blog Section Title: {website_data.get('blogSectionTitle')}")
        print(f"Customizations: {website_data.get('customizations')}")
        print(f"Status: {website_data.get('status')}")
        
        print("\n=== ALL FIELDS ===")
        for key, value in website_data.items():
            print(f"{key}: {value}")
        
        # Test hero image URL
        if website_data.get('heroImage'):
            print(f"\n6. Testing hero image URL accessibility...")
            hero_url = website_data['heroImage']
            try:
                img_response = requests.head(hero_url, timeout=10)
                if img_response.status_code == 200:
                    print(f"✅ Hero image URL is accessible: {hero_url}")
                else:
                    print(f"❌ Hero image URL returned status {img_response.status_code}: {hero_url}")
            except Exception as e:
                print(f"❌ Hero image URL test failed: {e}")
        else:
            print("❌ No hero image found in website data!")
        
        return True
    else:
        print(f"❌ Website retrieval failed: {response.text}")
        return False

if __name__ == "__main__":
    test_website_data()