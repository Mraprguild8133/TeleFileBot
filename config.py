"""
Configuration management for the Telegram bot
"""

import os
import logging
from typing import List

logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        """Initialize configuration from environment variables"""
        
        # Required Telegram API credentials
        self.API_ID = int(os.getenv("API_ID", "0"))
        self.API_HASH = os.getenv("API_HASH", "")
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "")
        
        # Admin and Owner IDs
        self.OWNER_ID = int(os.getenv("OWNER_ID", "0"))
        self.ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
        
        # Create admin list (owner + admin)
        self.ADMIN_IDS = [self.OWNER_ID]
        if self.ADMIN_ID != 0 and self.ADMIN_ID != self.OWNER_ID:
            self.ADMIN_IDS.append(self.ADMIN_ID)
        
        # Storage configuration
        self.STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID", "0"))
        self.DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_data.db")
        self.FILES_DIR = os.getenv("FILES_DIR", "files")
        self.TEMP_DIR = os.getenv("TEMP_DIR", "temp")
        
        # URL Shortener configuration
        self.CUSTOM_DOMAIN = os.getenv("CUSTOM_DOMAIN", "")
        self.API_KEY = os.getenv("API_KEY", "")
        self.SHORT_URL_LENGTH = int(os.getenv("SHORT_URL_LENGTH", "6"))
        
        # File handling configuration
        self.MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB in bytes
        self.CHUNK_SIZE = 1024 * 1024  # 1MB chunks for upload
        
        # Bot configuration
        self.BOT_NAME = os.getenv("BOT_NAME", "Mraprguild URL & File Bot")
        self.BOT_USERNAME = os.getenv("BOT_USERNAME", "")
        
        # Validate required fields
        self._validate_config()
    
    def _validate_config(self):
        """Validate required configuration fields"""
        errors = []
        
        if self.API_ID == 0:
            errors.append("API_ID is required")
        
        if not self.API_HASH:
            errors.append("API_HASH is required")
        
        if not self.BOT_TOKEN:
            errors.append("BOT_TOKEN is required")
        
        if self.OWNER_ID == 0:
            errors.append("OWNER_ID is required")
        
        if errors:
            error_msg = "Missing required environment variables:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validated successfully")
    
    def get_info(self) -> dict:
        """Get configuration info for status display"""
        return {
            "api_id": self.API_ID,
            "owner_id": self.OWNER_ID,
            "admin_ids": self.ADMIN_IDS,
            "storage_channel": self.STORAGE_CHANNEL_ID,
            "custom_domain": self.CUSTOM_DOMAIN,
            "max_file_size": f"{self.MAX_FILE_SIZE / (1024**3):.1f}GB",
            "bot_name": self.BOT_NAME
        }
