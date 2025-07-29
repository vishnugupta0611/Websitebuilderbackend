from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    register, verify_otp, login, logout, profile, dashboard_analytics,
    WebsiteViewSet, BlogPostViewSet, ProductViewSet, OrderViewSet, CartViewSet
)

router = DefaultRouter()
router.register(r'websites', WebsiteViewSet, basename='website')
router.register(r'blogs', BlogPostViewSet, basename='blog')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'cart', CartViewSet, basename='cart')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', register, name='register'),
    path('auth/verify-otp/', verify_otp, name='verify_otp'),
    path('auth/login/', login, name='login'),
    path('auth/logout/', logout, name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', profile, name='profile'),
    
    # Analytics
    path('analytics/dashboard/', dashboard_analytics, name='dashboard_analytics'),
    
    # Include router URLs
    path('', include(router.urls)),
]
