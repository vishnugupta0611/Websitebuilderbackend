#!/usr/bin/env python3
import requests
import json
import random

# Test blog API endpoints
def test_blog_api():
    print("🚀 Testing Blog API...")
    
    # First, register and login to get auth token
    register_data = {
        "firstName": "Blog",
        "lastName": "Tester", 
        "email": f"blog.tester{random.randint(1000, 9999)}@example.com",
        "phone": "1234567890",
        "password": "MyStr0ngP@ssw0rd123!",
        "confirmPassword": "MyStr0ngP@ssw0rd123!"
    }
    
    headers = {"Content-Type": "application/json"}
    
    # Register user
    print("\n1. Registering test user...")
    register_response = requests.post("http://localhost:8000/api/auth/register/", json=register_data, headers=headers)
    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.text}")
        return
    
    print("✅ User registered successfully")
    
    # Verify OTP
    print("\n2. Verifying OTP...")
    otp_data = {"email": register_data["email"], "otp": "123456"}
    otp_response = requests.post("http://localhost:8000/api/auth/verify-otp/", json=otp_data, headers=headers)
    if otp_response.status_code != 200:
        print(f"❌ OTP verification failed: {otp_response.text}")
        return
    
    otp_result = otp_response.json()
    access_token = otp_result['tokens']['access']
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    print("✅ OTP verified, got access token")
    
    # Create a website first
    print("\n3. Creating test website...")
    website_data = {
        "name": "Test Blog Website",
        "slug": f"test-blog-site-{random.randint(1000, 9999)}",
        "description": "A test website for blog testing",
        "category": "business",
        "status": "published",
        "customizations": {
            "colors": {
                "primary": "#10b981",
                "secondary": "#6b7280",
                "accent": "#f59e0b",
                "background": "#ffffff",
                "text": "#111827"
            },
            "typography": {
                "headingFont": "Inter",
                "bodyFont": "Inter"
            }
        }
    }
    
    website_response = requests.post("http://localhost:8000/api/websites/", json=website_data, headers=auth_headers)
    if website_response.status_code != 201:
        print(f"❌ Website creation failed: {website_response.text}")
        return
    
    website_result = website_response.json()
    website_id = website_result['id']
    print(f"✅ Website created with ID: {website_id}")
    
    # Test blog creation
    print("\n4. Creating test blog...")
    blog_data = {
        "title": "Test Blog Post",
        "slug": "test-blog-post",
        "excerpt": "This is a test blog post excerpt",
        "content": "This is the full content of the test blog post. It contains multiple paragraphs and detailed information.",
        "featuredImage": "https://via.placeholder.com/600x400/10b981/white?text=Test+Blog",
        "tags": ["test", "blog", "api"],
        "author": "Blog Tester",
        "status": "published",
        "layout": "column",
        "website": website_id,
        "customizations": {
            "showAuthor": True,
            "showDate": True,
            "showTags": True,
            "layout": "column"
        }
    }
    
    blog_response = requests.post("http://localhost:8000/api/blogs/", json=blog_data, headers=auth_headers)
    print(f"Blog creation status: {blog_response.status_code}")
    print(f"Blog creation response: {blog_response.text}")
    
    if blog_response.status_code != 201:
        print(f"❌ Blog creation failed: {blog_response.text}")
        return
    
    blog_result = blog_response.json()
    blog_id = blog_result['id']
    print(f"✅ Blog created with ID: {blog_id}")
    
    # Test blog update
    print("\n5. Testing blog update...")
    update_data = {
        "title": "Updated Test Blog Post",
        "slug": "updated-test-blog-post",
        "excerpt": "This is an updated test blog post excerpt",
        "content": "This is the updated full content of the test blog post. It has been modified with new information.",
        "featuredImage": "https://via.placeholder.com/600x400/f59e0b/white?text=Updated+Blog",
        "tags": ["updated", "test", "blog", "api"],
        "author": "Blog Tester",
        "status": "published",
        "layout": "hover-overlay",
        "website": website_id,
        "customizations": {
            "showAuthor": True,
            "showDate": True,
            "showTags": True,
            "layout": "hover-overlay"
        }
    }
    
    update_response = requests.put(f"http://localhost:8000/api/blogs/{blog_id}/", json=update_data, headers=auth_headers)
    print(f"Blog update status: {update_response.status_code}")
    print(f"Blog update response: {update_response.text}")
    
    if update_response.status_code == 200:
        print("✅ Blog updated successfully")
        updated_blog = update_response.json()
        print(f"Updated title: {updated_blog['title']}")
        print(f"Updated layout: {updated_blog.get('layout', 'Not found')}")
    else:
        print(f"❌ Blog update failed: {update_response.text}")
    
    # Test blog retrieval
    print("\n6. Testing blog retrieval...")
    get_response = requests.get(f"http://localhost:8000/api/blogs/{blog_id}/", headers=auth_headers)
    if get_response.status_code == 200:
        print("✅ Blog retrieved successfully")
        blog_data = get_response.json()
        print(f"Title: {blog_data['title']}")
        print(f"Status: {blog_data['status']}")
        print(f"Layout: {blog_data['layout']}")
    else:
        print(f"❌ Blog retrieval failed: {get_response.text}")
    
    # Test public blog access
    print("\n7. Testing public blog access...")
    public_response = requests.get(f"http://localhost:8000/api/blogs/by_website_slug/?slug=test-blog-site")
    if public_response.status_code == 200:
        print("✅ Public blog access successful")
        public_blogs = public_response.json()
        print(f"Found {len(public_blogs)} published blogs")
    else:
        print(f"❌ Public blog access failed: {public_response.text}")
    
    print("\n🎉 Blog API testing completed!")

if __name__ == "__main__":
    test_blog_api()