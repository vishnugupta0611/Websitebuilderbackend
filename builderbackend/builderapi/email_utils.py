"""
Email utilities for sending beautiful, professional emails
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_otp_email(user, otp_code):
    """
    Send a beautiful, professional OTP verification email
    
    Args:
        user: User instance
        otp_code: 6-digit OTP code
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Email subject
        subject = f"🔐 Verify Your Corporate Portal Account - Code: {otp_code}"
        
        # Render HTML template
        html_content = render_to_string('emails/otp_verification.html', {
            'user_name': f"{user.firstName} {user.lastName}",
            'user_email': user.email,
            'otp_code': otp_code,
        })
        
        # Create plain text version
        text_content = f"""
Corporate Portal - Email Verification

Hello {user.firstName} {user.lastName},

Welcome to Corporate Portal! To complete your account registration, please verify your email address using the verification code below:

VERIFICATION CODE: {otp_code}

This code expires in 10 minutes.

How to verify your account:
1. Return to the Corporate Portal registration page
2. Enter the 6-digit verification code above
3. Click "Verify Email" to complete your registration
4. Start building your professional websites!

Security Notice: This verification code is valid for 10 minutes only. If you didn't request this verification, please ignore this email.

Thank you for choosing Corporate Portal!

---
Corporate Portal
Professional Website Builder & E-commerce Platform
© 2025 Corporate Portal. All rights reserved.
        """.strip()
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        logger.info(f"OTP email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send OTP email to {user.email}: {str(e)}")
        return False

def send_welcome_email(user):
    """
    Send a welcome email after successful verification
    
    Args:
        user: User instance
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = "🎉 Welcome to Corporate Portal - Your Account is Ready!"
        
        # Create welcome message
        text_content = f"""
Welcome to Corporate Portal, {user.firstName}!

Your account has been successfully verified and is now ready to use.

What you can do now:
• Create professional websites with our drag-and-drop builder
• Set up e-commerce stores and manage products
• Write and publish blog posts
• Track orders and analytics
• Customize your brand with themes and templates

Get started: Log in to your account and explore our powerful website building tools.

If you have any questions, our support team is here to help.

Welcome aboard!

---
Corporate Portal Team
Professional Website Builder & E-commerce Platform
        """.strip()
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        
        # Send email
        email.send()
        
        logger.info(f"Welcome email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False