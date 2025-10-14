import time
import hashlib
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


def get_rate_limit_key(request, action, identifier=None):
    """Generate a unique cache key for rate limiting"""
    client_ip = get_client_ip(request)
    user_id = request.user.id if request.user.is_authenticated else 'anonymous'
    
    # Use session key as additional identifier for anonymous users
    session_key = request.session.session_key or 'no_session'
    
    if identifier:
        base_string = f"rate_limit:{action}:{client_ip}:{user_id}:{session_key}:{identifier}"
    else:
        base_string = f"rate_limit:{action}:{client_ip}:{user_id}:{session_key}"
    
    # Create a hash to ensure consistent key length
    return hashlib.md5(base_string.encode()).hexdigest()


class CartRateLimiter:
    """Rate limiter specifically for cart operations"""
    
    # Default rate limits (requests per time period)
    DEFAULT_LIMITS = {
        'cart_add': {'requests': 30, 'window': 300},  # 30 requests per 5 minutes
        'cart_checkout': {'requests': 5, 'window': 300},  # 5 checkouts per 5 minutes
        'promo_apply': {'requests': 10, 'window': 300},  # 10 promo attempts per 5 minutes
        'quantity_change': {'requests': 50, 'window': 300},  # 50 quantity changes per 5 minutes
        'item_remove': {'requests': 20, 'window': 300},  # 20 item removals per 5 minutes
    }
    
    @classmethod
    def get_limit_config(cls, action):
        """Get rate limit configuration for an action"""
        return getattr(settings, 'CART_RATE_LIMITS', cls.DEFAULT_LIMITS).get(
            action, cls.DEFAULT_LIMITS.get(action, {'requests': 10, 'window': 300})
        )
    
    @classmethod
    def is_rate_limited(cls, request, action, identifier=None):
        """
        Check if request should be rate limited
        
        Args:
            request: Django request object
            action: Action being performed (e.g., 'cart_add', 'checkout')
            identifier: Optional additional identifier (e.g., cart_id, ticket_id)
            
        Returns:
            tuple: (is_limited, remaining_requests, reset_time)
        """
        config = cls.get_limit_config(action)
        max_requests = config['requests']
        window_seconds = config['window']
        
        cache_key = get_rate_limit_key(request, action, identifier)
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Get current request data from cache
        request_data = cache.get(cache_key, [])
        
        # Filter out old requests outside the time window
        recent_requests = [req_time for req_time in request_data if req_time > window_start]
        
        # Check if limit is exceeded
        if len(recent_requests) >= max_requests:
            oldest_request = min(recent_requests) if recent_requests else current_time
            reset_time = oldest_request + window_seconds
            return True, 0, reset_time
        
        # Add current request
        recent_requests.append(current_time)
        
        # Store updated request data
        cache.set(cache_key, recent_requests, window_seconds + 60)  # Extra 60 seconds buffer
        
        remaining = max_requests - len(recent_requests)
        reset_time = current_time + window_seconds
        
        return False, remaining, reset_time
    
    @classmethod
    def log_rate_limit_attempt(cls, request, action, identifier=None):
        """Log rate limiting attempt for monitoring"""
        client_ip = get_client_ip(request)
        user_info = f"User {request.user.id}" if request.user.is_authenticated else "Anonymous"
        
        logger.warning(
            f"Rate limit exceeded for {action} - "
            f"IP: {client_ip}, {user_info}, "
            f"Identifier: {identifier or 'None'}"
        )


def rate_limit(action, per_user=True, identifier_func=None):
    """
    Decorator for rate limiting views
    
    Args:
        action: The action name for rate limiting
        per_user: Whether to apply limits per user (default) or globally
        identifier_func: Function to extract additional identifier from request
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Extract identifier if function provided
            identifier = None
            if identifier_func:
                try:
                    identifier = identifier_func(request, *args, **kwargs)
                except Exception as e:
                    logger.warning(f"Failed to extract identifier for rate limiting: {e}")
            
            # Check rate limit
            is_limited, remaining, reset_time = CartRateLimiter.is_rate_limited(
                request, action, identifier
            )
            
            if is_limited:
                CartRateLimiter.log_rate_limit_attempt(request, action, identifier)
                
                # Return JSON response for AJAX requests
                if request.headers.get('Content-Type') == 'application/json' or \
                   request.headers.get('Accept', '').startswith('application/json'):
                    return JsonResponse({
                        'error': 'Rate limit exceeded. Please try again later.',
                        'rate_limited': True,
                        'reset_time': int(reset_time)
                    }, status=429)
                else:
                    # For regular requests, you might want to render a template
                    from django.shortcuts import render
                    return render(request, 'cart/rate_limit_exceeded.html', {
                        'reset_time': int(reset_time),
                        'action': action
                    }, status=429)
            
            # Add rate limit headers to response
            response = view_func(request, *args, **kwargs)
            
            if hasattr(response, '__setitem__'):  # Check if response supports headers
                response['X-RateLimit-Limit'] = CartRateLimiter.get_limit_config(action)['requests']
                response['X-RateLimit-Remaining'] = remaining
                response['X-RateLimit-Reset'] = int(reset_time)
            
            return response
        
        return wrapper
    return decorator


# Specific identifier functions for different cart operations
def get_cart_identifier(request, *args, **kwargs):
    """Extract cart ID for rate limiting"""
    try:
        from .views import _cart_id
        return _cart_id(request)
    except:
        return None


def get_item_identifier(request, *args, **kwargs):
    """Extract item ID from URL parameters"""
    return kwargs.get('item_id')


def get_ticket_identifier(request, *args, **kwargs):
    """Extract ticket ID from request data"""
    try:
        import json
        data = json.loads(request.body)
        tickets = data.get('tickets', [])
        if tickets and len(tickets) > 0:
            return str(tickets[0].get('id', ''))
    except:
        pass
    return None