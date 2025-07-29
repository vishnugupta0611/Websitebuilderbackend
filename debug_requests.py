#!/usr/bin/env python3
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import logging

# Set up logging to see what's being received
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def debug_register(request):
    """Debug endpoint to see what data is being sent"""
    logger.debug(f"Request method: {request.method}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    logger.debug(f"Request body: {request.body}")
    logger.debug(f"Request content type: {request.content_type}")
    
    try:
        data = json.loads(request.body)
        logger.debug(f"Parsed JSON data: {data}")
    except Exception as e:
        logger.debug(f"Failed to parse JSON: {e}")
    
    return JsonResponse({"debug": "received"})

# Add this to your Django URLs temporarily to debug
print("Add this to your urls.py:")
print("path('debug/register/', debug_register, name='debug_register'),")