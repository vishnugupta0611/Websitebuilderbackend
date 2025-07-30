from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Website, BlogPost, Product, Order, Cart, OTPVerification
import random
import string

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirmPassword = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['firstName', 'lastName', 'email', 'phone', 'password', 'confirmPassword']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirmPassword']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirmPassword')
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            firstName=validated_data['firstName'],
            lastName=validated_data['lastName'],
            phone=validated_data.get('phone', ''),
            password=validated_data['password']
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password')
            if not user.isVerified:
                raise serializers.ValidationError('Please verify your email first')
            attrs['user'] = user
        return attrs

class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)
    
    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('OTP must be 6 digits')
        return value

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'firstName', 'lastName', 'email', 'phone', 'company', 'addresses', 'isVerified', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'isVerified', 'createdAt', 'updatedAt']

class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Website
        fields = '__all__'
        read_only_fields = ['user', 'createdAt', 'updatedAt']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = '__all__'
        read_only_fields = ['createdAt', 'updatedAt']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['createdAt', 'updatedAt']

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['createdAt', 'updatedAt']

class CartSerializer(serializers.ModelSerializer):
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = '__all__'
        read_only_fields = ['user', 'addedAt']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class CheckoutSerializer(serializers.Serializer):
    customerName = serializers.CharField(max_length=200)
    customerEmail = serializers.EmailField()
    customerPhone = serializers.CharField(max_length=20)
    customerAddress = serializers.CharField()
    customerCity = serializers.CharField(max_length=100)
    customerZipCode = serializers.CharField(max_length=20)
    websiteSlug = serializers.CharField(max_length=200)
    websiteName = serializers.CharField(max_length=200)
