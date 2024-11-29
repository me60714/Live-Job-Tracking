#######################################################################
# This script implements a rate limiter for Jira API requests.        #
#######################################################################

import time
from datetime import datetime, timedelta
import logging

class RateLimiter:
    def __init__(self, requests_per_minute=50, buffer_percentage=0.1): # 50 requests per minute, 10% buffer
        self.requests_per_minute = requests_per_minute
        self.buffer = int(requests_per_minute * buffer_percentage)  # Safety buffer
        self.requests = []
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for rate limiter."""
        self.logger = logging.getLogger('RateLimiter')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def wait_if_needed(self):
        """Check and wait if we're approaching rate limits."""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests if req_time > minute_ago]
        
        # If we're approaching the limit (including buffer), wait
        if len(self.requests) >= (self.requests_per_minute - self.buffer):
            oldest_request = self.requests[0]
            sleep_time = (oldest_request + timedelta(minutes=1) - now).total_seconds()
            if sleep_time > 0:
                self.logger.info(f"Rate limit approaching. Waiting {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
        
        # Add current request
        self.requests.append(now)
    
    def update_limit(self, remaining: int):
        """Update rate limiting based on headers from Jira."""
        if remaining < self.buffer:
            self.logger.warning(f"Very low on remaining requests: {remaining}")
            time.sleep(2)  # Add extra delay when close to limit
    
    def get_current_usage(self) -> dict:
        """Get current rate limit usage statistics."""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        current_requests = len([req for req in self.requests if req > minute_ago])
        
        return {
            'current_requests': current_requests,
            'limit': self.requests_per_minute,
            'remaining': self.requests_per_minute - current_requests,
            'buffer': self.buffer
        }