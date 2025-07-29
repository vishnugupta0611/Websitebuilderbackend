from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import Q
import random
import string

from .models import User, Website, BlogPost, Product, Order, Cart, OTPVerification
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, OTPVerificationSerializer,
    UserSerializer, WebsiteSerializer, BlogPostSerializer, ProductSerializer,
    OrderSerializer, CartSerializer, CheckoutSerializer
)

# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate OTP
        otp = ''.join(random.choices(string.digits, k=6))
        OTPVerification.objects.create(user=user, otp=otp)
        
        # Send OTP email (in console for development)
        try:
            send_mail(
                'Verify Your Email - Corporate Portal',
                f'Your OTP verification code is: {otp}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Email sending failed: {e}")
        
        return Response({
            'message': 'User registered successfully. Please check your email for OTP verification.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    serializer = OTPVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        
        try:
            user = User.objects.get(email=email)
            
            # BYPASS OTP VERIFICATION - Accept any 6-digit OTP for development
            if len(otp) == 6 and otp.isdigit():
                # Mark user as verified
                user.isVerified = True
                user.save()
                
                # Mark any existing OTP as used
                OTPVerification.objects.filter(user=user, is_used=False).update(is_used=True)
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'message': 'Email verified successfully',
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Please enter a valid 6-digit OTP'}, status=status.HTTP_400_BAD_REQUEST)
            
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request):
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Website Management Views
class WebsiteViewSet(viewsets.ModelViewSet):
    serializer_class = WebsiteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Website.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def by_slug(self, request):
        slug = request.query_params.get('slug')
        if not slug:
            return Response({'error': 'Slug parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            website = Website.objects.get(slug=slug)
            serializer = self.get_serializer(website)
            return Response(serializer.data)
        except Website.DoesNotExist:
            return Response({'error': 'Website not found'}, status=status.HTTP_404_NOT_FOUND)

# Blog Management Views
class BlogPostViewSet(viewsets.ModelViewSet):
    serializer_class = BlogPostSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        website_id = self.request.query_params.get('website')
        if website_id:
            return BlogPost.objects.filter(website_id=website_id, website__user=self.request.user)
        return BlogPost.objects.filter(website__user=self.request.user)
    
    def perform_create(self, serializer):
        # Ensure the website belongs to the current user
        website_id = serializer.validated_data['website'].id
        website = Website.objects.get(id=website_id, user=self.request.user)
        serializer.save()
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def by_website_slug(self, request):
        slug = request.query_params.get('slug')
        if not slug:
            return Response({'error': 'Slug parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            website = Website.objects.get(slug=slug)
            blogs = BlogPost.objects.filter(website=website, status='published')
            serializer = self.get_serializer(blogs, many=True)
            return Response(serializer.data)
        except Website.DoesNotExist:
            return Response({'error': 'Website not found'}, status=status.HTTP_404_NOT_FOUND)

# Product Management Views
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        website_id = self.request.query_params.get('website')
        if website_id:
            return Product.objects.filter(website_id=website_id, website__user=self.request.user)
        return Product.objects.filter(website__user=self.request.user)
    
    def perform_create(self, serializer):
        # Ensure the website belongs to the current user
        website_id = serializer.validated_data['website'].id
        website = Website.objects.get(id=website_id, user=self.request.user)
        serializer.save()
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def by_website_slug(self, request):
        slug = request.query_params.get('slug')
        if not slug:
            return Response({'error': 'Slug parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            website = Website.objects.get(slug=slug)
            products = Product.objects.filter(website=website, status='active')
            serializer = self.get_serializer(products, many=True)
            return Response(serializer.data)
        except Website.DoesNotExist:
            return Response({'error': 'Website not found'}, status=status.HTTP_404_NOT_FOUND)

# Order Management Views
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(website__user=self.request.user)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def create_order(self, request):
        serializer = CheckoutSerializer(data=request.data)
        if serializer.is_valid():
            # Get user's cart items for the specific website
            website_slug = serializer.validated_data['websiteSlug']
            
            try:
                website = Website.objects.get(slug=website_slug)
            except Website.DoesNotExist:
                return Response({'error': 'Website not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # For anonymous users, we'll need to handle cart items from request
            cart_items = request.data.get('items', [])
            
            if not cart_items:
                return Response({'error': 'No items in cart'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate total
            total = sum(item['price'] * item['quantity'] for item in cart_items)
            
            # Create order
            order = Order.objects.create(
                website=website,
                websiteSlug=website_slug,
                websiteName=serializer.validated_data['websiteName'],
                items=cart_items,
                total=total,
                customerName=serializer.validated_data['customerName'],
                customerEmail=serializer.validated_data['customerEmail'],
                customerPhone=serializer.validated_data['customerPhone'],
                customerAddress=serializer.validated_data['customerAddress'],
                customerCity=serializer.validated_data['customerCity'],
                customerZipCode=serializer.validated_data['customerZipCode'],
            )
            
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Cart Management Views
class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def add_to_cart(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Check if item already exists in cart
            existing_item = Cart.objects.filter(
                user=request.user,
                product_id=serializer.validated_data['product_id'],
                websiteSlug=serializer.validated_data['websiteSlug']
            ).first()
            
            if existing_item:
                existing_item.quantity += serializer.validated_data['quantity']
                existing_item.save()
                return Response(CartSerializer(existing_item).data)
            else:
                cart_item = serializer.save()
                return Response(CartSerializer(cart_item).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def clear_cart(self, request):
        website_slug = request.query_params.get('website_slug')
        if website_slug:
            Cart.objects.filter(user=request.user, websiteSlug=website_slug).delete()
        else:
            Cart.objects.filter(user=request.user).delete()
        return Response({'message': 'Cart cleared successfully'}, status=status.HTTP_200_OK)

# Analytics Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_analytics(request):
    user_websites = Website.objects.filter(user=request.user)
    
    analytics = {
        'total_websites': user_websites.count(),
        'total_products': Product.objects.filter(website__user=request.user).count(),
        'total_orders': Order.objects.filter(website__user=request.user).count(),
        'total_revenue': sum(order.total for order in Order.objects.filter(website__user=request.user)),
        'pending_orders': Order.objects.filter(website__user=request.user, status='pending').count(),
        'completed_orders': Order.objects.filter(website__user=request.user, status='delivered').count(),
    }
    
    return Response(analytics)
