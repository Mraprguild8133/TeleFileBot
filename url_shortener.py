"""
URL Shortening functionality
"""

import random
import string
import re
import logging
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class URLShortener:
    def __init__(self, database, custom_domain: str = "", length: int = 6):
        """Initialize URL shortener"""
        self.database = database
        self.custom_domain = custom_domain
        self.length = length
        self.base_url = custom_domain if custom_domain else "https://short.ly"
    
    def generate_short_code(self, length: int = None) -> str:
        """Generate a random short code"""
        if length is None:
            length = self.length
        
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
    
    async def create_short_code(self) -> str:
        """Create a unique short code"""
        max_attempts = 100
        
        for _ in range(max_attempts):
            code = self.generate_short_code()
            
            # Check if code already exists
            existing_url = await self.database.get_original_url(code)
            if not existing_url:
                return code
        
        # If we couldn't find a unique code, increase length
        return self.generate_short_code(self.length + 1)
    
    def is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def clean_url(self, url: str) -> str:
        """Clean and normalize URL"""
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    async def shorten_url(self, user_id: int, original_url: str) -> Optional[str]:
        """Shorten a URL"""
        try:
            # Clean and validate URL
            cleaned_url = self.clean_url(original_url)
            
            if not self.is_valid_url(cleaned_url):
                logger.warning(f"Invalid URL: {original_url}")
                return None
            
            # Generate unique short code
            short_code = await self.create_short_code()
            
            # Save to database
            success = await self.database.add_short_url(
                user_id, cleaned_url, short_code, self.custom_domain
            )
            
            if success:
                # Return shortened URL
                short_url = f"{self.base_url}/{short_code}"
                logger.info(f"Created short URL: {short_url} -> {cleaned_url}")
                return short_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error shortening URL: {e}")
            return None
    
    async def expand_url(self, short_code: str) -> Optional[str]:
        """Expand a short URL"""
        try:
            original_url = await self.database.get_original_url(short_code)
            
            if original_url:
                logger.info(f"Expanded: {short_code} -> {original_url}")
            
            return original_url
            
        except Exception as e:
            logger.error(f"Error expanding URL {short_code}: {e}")
            return None
    
    def extract_urls_from_text(self, text: str) -> list:
        """Extract URLs from text"""
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        return url_pattern.findall(text)
    
    async def update_custom_domain(self, domain: str):
        """Update custom domain"""
        self.custom_domain = domain
        self.base_url = domain if domain else "https://short.ly"
        
        # Save to database
        await self.database.set_setting("custom_domain", domain)
        logger.info(f"Updated custom domain to: {domain}")
    
    async def get_url_stats(self, user_id: int) -> dict:
        """Get URL statistics for a user"""
        try:
            cursor = await self.database.connection.execute("""
                SELECT COUNT(*), SUM(click_count) 
                FROM short_urls WHERE user_id = ?
            """, (user_id,))
            
            result = await cursor.fetchone()
            
            return {
                'total_urls': result[0] if result[0] else 0,
                'total_clicks': result[1] if result[1] else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting URL stats: {e}")
            return {'total_urls': 0, 'total_clicks': 0}
