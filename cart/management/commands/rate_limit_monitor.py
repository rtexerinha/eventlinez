from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone
import hashlib
import time
from collections import defaultdict


class Command(BaseCommand):
    help = 'Monitor cart rate limiting statistics and manage rate limits'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['stats', 'clear', 'clear-user', 'list-keys'],
            default='stats',
            help='Action to perform: stats, clear, clear-user, or list-keys'
        )
        parser.add_argument(
            '--user-ip',
            type=str,
            help='IP address to clear rate limits for (use with --action clear-user)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show verbose output'
        )

    def handle(self, *args, **options):
        action = options['action']
        verbose = options['verbose']

        if action == 'stats':
            self.show_rate_limit_stats(verbose)
        elif action == 'clear':
            self.clear_all_rate_limits()
        elif action == 'clear-user':
            if not options['user_ip']:
                self.stdout.write(
                    self.style.ERROR('--user-ip is required with --action clear-user')
                )
                return
            self.clear_user_rate_limits(options['user_ip'])
        elif action == 'list-keys':
            self.list_rate_limit_keys()

    def show_rate_limit_stats(self, verbose=False):
        """Show current rate limiting statistics"""
        self.stdout.write(self.style.SUCCESS('=== Cart Rate Limiting Statistics ==='))
        
        # Get all cache keys that start with 'rate_limit:'
        try:
            # This is implementation-specific and may not work with all cache backends
            cache_keys = []
            if hasattr(cache, '_cache'):  # LocMemCache
                cache_keys = [key for key in cache._cache.keys() if key.startswith('rate_limit:')]
            
            if not cache_keys:
                self.stdout.write('No active rate limits found.')
                return

            # Analyze rate limit data
            stats = defaultdict(lambda: {'count': 0, 'active_limits': 0, 'users': set()})
            current_time = time.time()
            
            for key in cache_keys:
                # Parse the key to extract action
                parts = key.split(':')
                if len(parts) >= 2:
                    action = parts[1]
                    ip = parts[2] if len(parts) > 2 else 'unknown'
                    
                    # Get the request data
                    requests = cache.get(key, [])
                    recent_requests = [req for req in requests if req > (current_time - 300)]  # 5 minutes
                    
                    stats[action]['count'] += len(recent_requests)
                    stats[action]['users'].add(ip)
                    
                    if len(recent_requests) > 0:
                        stats[action]['active_limits'] += 1

            # Display stats
            for action, data in stats.items():
                self.stdout.write(f"\n{action.upper()}:")
                self.stdout.write(f"  Active rate limits: {data['active_limits']}")
                self.stdout.write(f"  Total recent requests: {data['count']}")
                self.stdout.write(f"  Unique users/IPs: {len(data['users'])}")
                
                if verbose and data['users']:
                    self.stdout.write(f"  IPs: {', '.join(list(data['users'])[:10])}")
                    if len(data['users']) > 10:
                        self.stdout.write(f"    ... and {len(data['users']) - 10} more")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error retrieving cache statistics: {e}')
            )

    def clear_all_rate_limits(self):
        """Clear all rate limiting data"""
        try:
            # Get all rate limit keys
            if hasattr(cache, '_cache'):  # LocMemCache
                keys_to_delete = [key for key in cache._cache.keys() if key.startswith('rate_limit:')]
                
                for key in keys_to_delete:
                    cache.delete(key)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Cleared {len(keys_to_delete)} rate limit entries.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Cache backend does not support key listing. Cannot clear all.')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error clearing rate limits: {e}')
            )

    def clear_user_rate_limits(self, user_ip):
        """Clear rate limits for a specific user IP"""
        try:
            cleared_count = 0
            if hasattr(cache, '_cache'):  # LocMemCache
                keys_to_delete = [
                    key for key in cache._cache.keys() 
                    if key.startswith('rate_limit:') and user_ip in key
                ]
                
                for key in keys_to_delete:
                    cache.delete(key)
                    cleared_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Cleared {cleared_count} rate limit entries for IP {user_ip}.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Cache backend does not support key listing.')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error clearing rate limits for user: {e}')
            )

    def list_rate_limit_keys(self):
        """List all rate limiting cache keys"""
        try:
            if hasattr(cache, '_cache'):  # LocMemCache
                keys = [key for key in cache._cache.keys() if key.startswith('rate_limit:')]
                
                self.stdout.write(f'Found {len(keys)} rate limit keys:')
                for key in keys[:20]:  # Show first 20
                    requests = cache.get(key, [])
                    self.stdout.write(f'  {key}: {len(requests)} requests')
                
                if len(keys) > 20:
                    self.stdout.write(f'  ... and {len(keys) - 20} more keys')
            else:
                self.stdout.write('Cache backend does not support key listing.')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error listing cache keys: {e}')
            )