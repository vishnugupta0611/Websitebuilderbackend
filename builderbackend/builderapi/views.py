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
from .email_utils import send_otp_email, send_welcome_email

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
        
        # Send beautiful OTP email
        email_sent = send_otp_email(user, otp)
        
        if not email_sent:
            return Response({
                'error': 'Failed to send verification email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': 'User registered successfully. Please check your email for OTP verification.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """Resend OTP to user's email"""
    email = request.data.get('email')
    
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        if user.isVerified:
            return Response({'error': 'User is already verified'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark all existing OTPs as used
        OTPVerification.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate new OTP
        otp = ''.join(random.choices(string.digits, k=6))
        OTPVerification.objects.create(user=user, otp=otp)
        
        # Send beautiful OTP email
        email_sent = send_otp_email(user, otp)
        
        if not email_sent:
            return Response({
                'error': 'Failed to send verification email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': 'New verification code sent to your email'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    serializer = OTPVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        
        try:
            user = User.objects.get(email=email)
            
            # Get the latest unused OTP for this user
            otp_verification = OTPVerification.objects.filter(
                user=user, 
                otp=otp, 
                is_used=False
            ).first()
            
            if not otp_verification:
                return Response({
                    'error': 'Invalid or expired OTP. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if OTP is expired (10 minutes)
            if otp_verification.is_expired():
                return Response({
                    'error': 'OTP has expired. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark OTP as used
            otp_verification.is_used = True
            otp_verification.save()
            
            # Mark user as verified
            user.isVerified = True
            user.save()
            
            # Send welcome email
            send_welcome_email(user)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Email verified successfully! Welcome to Corporate Portal.',
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
            
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
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def public_detail(self, request, pk=None):
        """Get product details for public access (subsite)"""
        try:
            # Validate that pk is a valid integer
            try:
                product_id = int(pk)
            except (ValueError, TypeError):
                return Response({'error': 'Invalid product ID'}, status=status.HTTP_400_BAD_REQUEST)
            
            product = Product.objects.get(pk=product_id, status='active')
            serializer = self.get_serializer(product)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def customer_orders(self, request):
        """Get orders for a specific customer by email and website slug"""
        email = request.query_params.get('email')
        website_slug = request.query_params.get('website_slug')
        
        if not email or not website_slug:
            return Response({
                'error': 'Both email and website_slug parameters are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get orders for this customer and website
            orders = Order.objects.filter(
                customerEmail=email,
                websiteSlug=website_slug
            ).order_by('-createdAt')
            
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                'error': f'Failed to fetch customer orders: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

# Search Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_content(request):
    """Search across websites, products, and blog posts"""
    query = request.GET.get('q', '').strip()
    content_type = request.GET.get('type', '')
    sort_by = request.GET.get('sortBy', 'relevance')
    
    if not query:
        return Response({
            'results': [],
            'total': 0,
            'query': query,
            'suggestions': []
        })
    
    results = []
    
    # Search websites
    if not content_type or content_type == 'page':
        websites = Website.objects.filter(
            user=request.user,
            name__icontains=query
        ) | Website.objects.filter(
            user=request.user,
            description__icontains=query
        )
        
        for website in websites:
            results.append({
                'id': f'website_{website.id}',
                'type': 'page',
                'title': website.name,
                'snippet': website.description[:200] + '...' if len(website.description) > 200 else website.description,
                'url': f'/{website.slug}',
                'lastModified': website.updatedAt.isoformat(),
                'relevance': calculate_relevance(query, website.name + ' ' + website.description)
            })
    
    # Search products
    if not content_type or content_type == 'product':
        products = Product.objects.filter(
            website__user=request.user,
            name__icontains=query
        ) | Product.objects.filter(
            website__user=request.user,
            description__icontains=query
        )
        
        for product in products:
            results.append({
                'id': f'product_{product.id}',
                'type': 'product',
                'title': product.name,
                'snippet': product.shortDescription or product.description[:200] + '...' if len(product.description) > 200 else product.description,
                'url': f'/{product.website.slug}/products/{product.id}',
                'lastModified': product.updatedAt.isoformat(),
                'price': float(product.price),
                'relevance': calculate_relevance(query, product.name + ' ' + product.description)
            })
    
    # Search blog posts
    if not content_type or content_type == 'blog':
        blogs = BlogPost.objects.filter(
            website__user=request.user,
            title__icontains=query
        ) | BlogPost.objects.filter(
            website__user=request.user,
            content__icontains=query
        )
        
        for blog in blogs:
            results.append({
                'id': f'blog_{blog.id}',
                'type': 'blog',
                'title': blog.title,
                'snippet': blog.excerpt or blog.content[:200] + '...' if len(blog.content) > 200 else blog.content,
                'url': f'/{blog.website.slug}/blogs/{blog.slug}',
                'lastModified': blog.updatedAt.isoformat(),
                'relevance': calculate_relevance(query, blog.title + ' ' + blog.content)
            })
    
    # Sort results
    if sort_by == 'relevance':
        results.sort(key=lambda x: x['relevance'], reverse=True)
    elif sort_by == 'date':
        results.sort(key=lambda x: x['lastModified'], reverse=True)
    elif sort_by == 'title':
        results.sort(key=lambda x: x['title'].lower())
    
    # Generate suggestions
    suggestions = generate_search_suggestions(query, request.user)
    
    return Response({
        'results': results,
        'total': len(results),
        'query': query,
        'suggestions': suggestions
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_suggestions(request):
    """Get search suggestions based on query"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return Response([])
    
    suggestions = generate_search_suggestions(query, request.user)
    return Response(suggestions)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def popular_searches(request):
    """Get popular search terms"""
    # For now, return static popular searches
    # In production, this would be based on actual search analytics
    popular = [
        {'query': 'products', 'count': 150},
        {'query': 'blog posts', 'count': 89},
        {'query': 'website', 'count': 76},
        {'query': 'business', 'count': 65},
        {'query': 'portfolio', 'count': 54}
    ]
    
    return Response(popular)

def calculate_relevance(query, content):
    """Calculate relevance score for search results"""
    if not query or not content:
        return 0.0
    
    query_lower = query.lower()
    content_lower = content.lower()
    
    # Exact match gets highest score
    if query_lower == content_lower:
        return 1.0
    
    # Title/name match gets high score
    if query_lower in content_lower[:100]:
        return 0.9
    
    # Count word matches
    query_words = query_lower.split()
    content_words = content_lower.split()
    
    matches = sum(1 for word in query_words if word in content_words)
    if len(query_words) > 0:
        return min(0.8, matches / len(query_words))
    
    return 0.1

def generate_search_suggestions(query, user):
    """Generate search suggestions based on user's content"""
    suggestions = []
    
    # Get unique words from user's websites
    websites = Website.objects.filter(user=user)
    for website in websites:
        words = (website.name + ' ' + website.description).lower().split()
        for word in words:
            if len(word) > 3 and query.lower() in word and word not in suggestions:
                suggestions.append(word)
    
    # Get unique words from user's products
    products = Product.objects.filter(website__user=user)
    for product in products:
        words = (product.name + ' ' + product.description).lower().split()
        for word in words:
            if len(word) > 3 and query.lower() in word and word not in suggestions:
                suggestions.append(word)
    
    # Limit to 5 suggestions
    return suggestions[:5]

# Customer Authentication Views (for subsite users)
@api_view(['POST'])
@permission_classes([AllowAny])
def customer_signup(request):
    """Customer signup for specific website"""
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirmPassword')
        first_name = request.data.get('firstName', '')
        last_name = request.data.get('lastName', '')
        phone = request.data.get('phone', '')
        website_slug = request.data.get('website_slug')
        
        # Handle both name formats (legacy and new)
        name = request.data.get('name')
        if not name and (first_name or last_name):
            name = f"{first_name} {last_name}".strip()
        
        if not all([email, password, website_slug]):
            return Response({
                'success': False,
                'error': 'Email, password, and website are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password confirmation if provided
        if confirm_password and password != confirm_password:
            return Response({
                'success': False,
                'error': 'Passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if website exists
        try:
            website = Website.objects.get(slug=website_slug)
        except Website.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Website not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'error': 'User with this email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use provided first/last names or split from name field
        if not first_name and not last_name and name:
            name_parts = name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Create user
        user = User.objects.create_user(
            username=email,  # Use email as username
            email=email,
            password=password,
            firstName=first_name,
            lastName=last_name,
            phone=phone,
            isVerified=False  # Will be verified via OTP
        )
        
        # Generate OTP
        otp = ''.join(random.choices(string.digits, k=6))
        OTPVerification.objects.create(user=user, otp=otp)
        
        # Send OTP email
        email_sent = send_otp_email(user, otp)
        
        if not email_sent:
            return Response({
                'success': False,
                'error': 'Failed to send verification email. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': True,
            'data': {
                'message': 'Account created successfully. Please check your email for verification code.',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': f"{user.firstName} {user.lastName}".strip(),
                    'isVerified': user.isVerified
                },
                'requires_verification': True
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def customer_login(request):
    """Customer login for specific website"""
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        website_slug = request.data.get('website_slug')
        
        if not all([email, password, website_slug]):
            return Response({
                'success': False,
                'error': 'Email, password, and website are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if website exists
        try:
            website = Website.objects.get(slug=website_slug)
        except Website.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Website not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Authenticate user
        user = authenticate(email=email, password=password)
        
        if not user:
            return Response({
                'success': False,
                'error': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.isVerified:
            return Response({
                'success': False,
                'error': 'Please verify your email before logging in',
                'requires_verification': True
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'data': {
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': f"{user.firstName} {user.lastName}".strip(),
                    'isVerified': user.isVerified
                },
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'website_slug': website_slug
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def customer_verify_otp(request):
    """Verify customer OTP for specific website"""
    try:
        email = request.data.get('email')
        otp = request.data.get('otp')
        website_slug = request.data.get('website_slug')
        
        if not all([email, otp, website_slug]):
            return Response({
                'success': False,
                'error': 'Email, OTP, and website are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if website exists
        try:
            website = Website.objects.get(slug=website_slug)
        except Website.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Website not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            user = User.objects.get(email=email)
            
            # Get the latest unused OTP for this user
            otp_verification = OTPVerification.objects.filter(
                user=user, 
                otp=otp, 
                is_used=False
            ).first()
            
            if not otp_verification:
                return Response({
                    'success': False,
                    'error': 'Invalid or expired OTP. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if OTP is expired (10 minutes)
            if otp_verification.is_expired():
                return Response({
                    'success': False,
                    'error': 'OTP has expired. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark OTP as used
            otp_verification.is_used = True
            otp_verification.save()
            
            # Mark user as verified
            user.isVerified = True
            user.save()
            
            # Send welcome email
            send_welcome_email(user)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'data': {
                    'message': 'Email verified successfully! Welcome!',
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'name': f"{user.firstName} {user.lastName}".strip(),
                        'isVerified': user.isVerified
                    },
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'website_slug': website_slug
                }
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def customer_profile(request):
    """Get or update customer profile"""
    try:
        website_slug = request.headers.get('X-Website-Slug')
        
        if not website_slug:
            return Response({
                'success': False,
                'error': 'Website context required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if website exists
        try:
            website = Website.objects.get(slug=website_slug)
        except Website.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Website not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            return Response({
                'success': True,
                'data': {
                    'id': request.user.id,
                    'email': request.user.email,
                    'name': f"{request.user.firstName} {request.user.lastName}".strip(),
                    'isVerified': request.user.isVerified,
                    'website_slug': website_slug
                }
            })
        
        elif request.method == 'PUT':
            name = request.data.get('name')
            
            if name:
                # Split name into first and last name
                name_parts = name.strip().split(' ', 1)
                request.user.firstName = name_parts[0]
                request.user.lastName = name_parts[1] if len(name_parts) > 1 else ''
                request.user.save()
            
            return Response({
                'success': True,
                'data': {
                    'id': request.user.id,
                    'email': request.user.email,
                    'name': f"{request.user.firstName} {request.user.lastName}".strip(),
                    'isVerified': request.user.isVerified,
                    'website_slug': website_slug
                }
            })
            
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def customer_logout(request):
    """Customer logout"""
    try:
        refresh_token = request.data.get("refresh_token")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'success': True,
            'data': {
                'message': 'Logout successful'
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': True,
            'data': {
                'message': 'Logout successful'
            }
        }, status=status.HTTP_200_OK)
