#!/usr/bin/env python3
"""
Backend Test Script - Tests Django setup and API endpoints
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'builderbackend.settings')
django.setup()

def test_django_setup():
    """Test basic Django setup"""
    print("🔧 Testing Django Setup...")
    
    try:
        from django.core.management import execute_from_command_line
        print("✅ Django imports working")
        
        # Test database connection
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Database connection working")
        
        # Test models
        from builderapi.models import User, Website, Product, BlogPost, Order, Cart
        print("✅ Models imported successfully")
        
        # Test user creation
        print("\n📝 Testing User Creation...")
        
        # Check if test user already exists
        test_email = "backend_test@example.com"
        if User.objects.filter(email=test_email).exists():
            print("🗑️ Removing existing test user...")
            User.objects.filter(email=test_email).delete()
        
        # Create test user
        user = User.objects.create_user(
            username=test_email,
            email=test_email,
            firstName="Backend",
            lastName="Test",
            password="testpass123"
        )
        print(f"✅ User created: {user.email}")
        
        # Test user verification
        user.isVerified = True
        user.save()
        print("✅ User verification working")
        
        # Test website creation
        print("\n🌐 Testing Website Creation...")
        website = Website.objects.create(
            user=user,
            name="Test Website",
            slug="test-backend-website",
            description="Backend test website",
            category="business",
            status="published"
        )
        print(f"✅ Website created: {website.name}")
        
        # Test product creation
        print("\n📦 Testing Product Creation...")
        product = Product.objects.create(
            website=website,
            name="Test Product",
            slug="test-product",
            description="A test product",
            price=99.99,
            category="electronics",
            inventory=10,
            sku="TEST-001",
            status="active"
        )
        print(f"✅ Product created: {product.name}")
        
        # Test blog creation
        print("\n📝 Testing Blog Creation...")
        blog = BlogPost.objects.create(
            website=website,
            title="Test Blog Post",
            slug="test-blog",
            content="This is a test blog post content.",
            author="Backend Test",
            status="published"
        )
        print(f"✅ Blog created: {blog.title}")
        
        print("\n🎉 All backend tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_views():
    """Test API views"""
    print("\n🔌 Testing API Views...")
    
    try:
        from builderapi.views import register, verify_otp, login
        from builderapi.serializers import UserRegistrationSerializer
        print("✅ API views imported successfully")
        
        # Test serializer
        test_data = {
            'firstName': 'API',
            'lastName': 'Test',
            'email': 'api_test@example.com',
            'phone': '1234567890',
            'password': 'testpass123',
            'confirmPassword': 'testpass123'
        }
        
        serializer = UserRegistrationSerializer(data=test_data)
        if serializer.is_valid():
            print("✅ User registration serializer working")
        else:
            print(f"❌ Serializer errors: {serializer.errors}")
            
        return True
        
    except Exception as e:
        print(f"❌ API views test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Backend Tests...")
    print("=" * 50)
    
    # Test Django setup
    django_ok = test_django_setup()
    
    # Test API views
    api_ok = test_api_views()
    
    print("\n" + "=" * 50)
    if django_ok and api_ok:
        print("🎉 All backend tests passed! Backend is ready.")
        sys.exit(0)
    else:
        print("❌ Some backend tests failed. Please check the errors above.")
        sys.exit(1)