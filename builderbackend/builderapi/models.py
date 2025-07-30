from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import json

class User(AbstractUser):
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=200, blank=True)
    addresses = models.JSONField(default=list)
    isVerified = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'firstName', 'lastName']
    
    def __str__(self):
        return f"{self.firstName} {self.lastName} ({self.email})"

class OTPVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=10)

class Website(models.Model):
    CATEGORY_CHOICES = [
        ('business', 'Business'),
        ('ecommerce', 'E-commerce'),
        ('portfolio', 'Portfolio'),
        ('blog', 'Blog'),
        ('restaurant', 'Restaurant'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='websites')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    logoUrl = models.URLField(blank=True)
    
    # Template information
    template_id = models.CharField(max_length=100, default='default')
    template_name = models.CharField(max_length=200, default='Default Template')
    template_metadata = models.JSONField(default=dict)
    
    # Template content
    heroTitle = models.CharField(max_length=200, blank=True)
    heroDescription = models.TextField(blank=True)
    heroImage = models.URLField(blank=True)
    heroButtonText = models.CharField(max_length=100, blank=True)
    productSectionTitle = models.CharField(max_length=200, blank=True)
    blogSectionTitle = models.CharField(max_length=200, blank=True)
    services = models.JSONField(default=list)
    contentBlocks = models.JSONField(default=list)
    
    # Theme and customizations
    theme = models.JSONField(default=dict)
    customizations = models.JSONField(default=dict)
    
    # About content
    companyStory = models.TextField(blank=True)
    whyCreated = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    features = models.JSONField(default=list)
    teamInfo = models.JSONField(default=list)
    contactInfo = models.JSONField(default=dict)
    
    # SEO
    seoTitle = models.CharField(max_length=200, blank=True)
    seoDescription = models.TextField(blank=True)
    seoKeywords = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.slug})"

class BlogPost(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='blog_posts')
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    featuredImage = models.URLField(blank=True)
    author = models.CharField(max_length=200)
    tags = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    publishDate = models.DateTimeField(null=True, blank=True)
    
    # Layout and customizations
    layout = models.CharField(max_length=50, default='column', choices=[
        ('column', 'Column'),
        ('row-image-left', 'Row (Image Left)'),
        ('row-image-right', 'Row (Image Right)'),
        ('hover-overlay', 'Hover Overlay'),
    ])
    template = models.JSONField(default=dict)
    customizations = models.JSONField(default=dict)
    
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['website', 'slug']
    
    def __str__(self):
        return f"{self.title} - {self.website.name}"

class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField()
    shortDescription = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    originalPrice = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=100)
    inventory = models.IntegerField(default=0)
    sku = models.CharField(max_length=100)
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Dimensions
    length = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    images = models.JSONField(default=list)
    variants = models.JSONField(default=list)
    
    # SEO
    seoTitle = models.CharField(max_length=200, blank=True)
    seoDescription = models.TextField(blank=True)
    seoKeywords = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['website', 'sku']
    
    def __str__(self):
        return f"{self.name} - {self.website.name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    website = models.ForeignKey(Website, on_delete=models.CASCADE, related_name='orders')
    websiteSlug = models.CharField(max_length=200)
    websiteName = models.CharField(max_length=200)
    
    # Order items
    items = models.JSONField(default=list)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Customer information
    customerName = models.CharField(max_length=200)
    customerEmail = models.EmailField()
    customerPhone = models.CharField(max_length=20)
    customerAddress = models.TextField()
    customerCity = models.CharField(max_length=100)
    customerZipCode = models.CharField(max_length=20)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.websiteName}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_image = models.URLField(blank=True)
    product_sku = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1)
    websiteSlug = models.CharField(max_length=200)
    websiteId = models.CharField(max_length=100)
    websiteName = models.CharField(max_length=200)
    addedAt = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity} - {self.user.email}"
    
    @property
    def total_price(self):
        return self.product_price * self.quantity
