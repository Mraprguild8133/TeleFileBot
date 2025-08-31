"""
Database management for the Telegram bot
"""

import sqlite3
import aiosqlite
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "bot_data.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.connection = None
        
    async def initialize(self):
        """Initialize database tables"""
        try:
            self.connection = await aiosqlite.connect(self.db_path)
            await self._create_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def _create_tables(self):
        """Create all necessary database tables"""
        
        # Users table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned BOOLEAN DEFAULT 0,
                total_files INTEGER DEFAULT 0,
                total_urls INTEGER DEFAULT 0
            )
        """)
        
        # URL shortening table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS short_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                original_url TEXT NOT NULL,
                short_code TEXT UNIQUE NOT NULL,
                custom_domain TEXT,
                click_count INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Files table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                file_id TEXT,
                message_id INTEGER,
                channel_message_id INTEGER,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                download_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Bot settings table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Statistics table
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_type TEXT NOT NULL,
                stat_value INTEGER DEFAULT 0,
                date DATE DEFAULT CURRENT_DATE
            )
        """)
        
        await self.connection.commit()
    
    async def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Add or update user information"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, first_name, last_name))
            await self.connection.commit()
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        try:
            cursor = await self.connection.execute("""
                SELECT * FROM users WHERE user_id = ?
            """, (user_id,))
            row = await cursor.fetchone()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def add_short_url(self, user_id: int, original_url: str, short_code: str, custom_domain: str = None) -> bool:
        """Add a shortened URL"""
        try:
            await self.connection.execute("""
                INSERT INTO short_urls (user_id, original_url, short_code, custom_domain)
                VALUES (?, ?, ?, ?)
            """, (user_id, original_url, short_code, custom_domain))
            
            # Update user URL count
            await self.connection.execute("""
                UPDATE users SET total_urls = total_urls + 1 WHERE user_id = ?
            """, (user_id,))
            
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding short URL: {e}")
            return False
    
    async def get_original_url(self, short_code: str) -> Optional[str]:
        """Get original URL from short code and increment click count"""
        try:
            cursor = await self.connection.execute("""
                SELECT original_url FROM short_urls WHERE short_code = ?
            """, (short_code,))
            row = await cursor.fetchone()
            
            if row:
                # Increment click count
                await self.connection.execute("""
                    UPDATE short_urls SET click_count = click_count + 1 WHERE short_code = ?
                """, (short_code,))
                await self.connection.commit()
                return row[0]
            return None
        except Exception as e:
            logger.error(f"Error getting original URL for {short_code}: {e}")
            return None
    
    async def add_file(self, user_id: int, file_name: str, file_size: int, file_type: str, 
                      file_id: str, message_id: int, channel_message_id: int = None) -> bool:
        """Add file information"""
        try:
            await self.connection.execute("""
                INSERT INTO files (user_id, file_name, file_size, file_type, file_id, 
                                 message_id, channel_message_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, file_name, file_size, file_type, file_id, message_id, channel_message_id))
            
            # Update user file count
            await self.connection.execute("""
                UPDATE users SET total_files = total_files + 1 WHERE user_id = ?
            """, (user_id,))
            
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding file: {e}")
            return False
    
    async def get_user_files(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's files"""
        try:
            cursor = await self.connection.execute("""
                SELECT * FROM files WHERE user_id = ? 
                ORDER BY upload_date DESC LIMIT ?
            """, (user_id, limit))
            rows = await cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting user files: {e}")
            return []
    
    async def set_setting(self, key: str, value: str):
        """Set bot setting"""
        try:
            await self.connection.execute("""
                INSERT OR REPLACE INTO bot_settings (key, value, updated_date)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
            await self.connection.commit()
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
    
    async def get_setting(self, key: str) -> Optional[str]:
        """Get bot setting"""
        try:
            cursor = await self.connection.execute("""
                SELECT value FROM bot_settings WHERE key = ?
            """, (key,))
            row = await cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return None
    
    async def get_statistics(self) -> Dict:
        """Get bot statistics"""
        try:
            stats = {}
            
            # Total users
            cursor = await self.connection.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = (await cursor.fetchone())[0]
            
            # Total URLs
            cursor = await self.connection.execute("SELECT COUNT(*) FROM short_urls")
            stats['total_urls'] = (await cursor.fetchone())[0]
            
            # Total files
            cursor = await self.connection.execute("SELECT COUNT(*) FROM files")
            stats['total_files'] = (await cursor.fetchone())[0]
            
            # Total clicks
            cursor = await self.connection.execute("SELECT SUM(click_count) FROM short_urls")
            result = await cursor.fetchone()
            stats['total_clicks'] = result[0] if result[0] else 0
            
            # Total file size
            cursor = await self.connection.execute("SELECT SUM(file_size) FROM files")
            result = await cursor.fetchone()
            stats['total_file_size'] = result[0] if result[0] else 0
            
            return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    async def get_all_users(self) -> List[int]:
        """Get all user IDs for broadcasting"""
        try:
            cursor = await self.connection.execute("""
                SELECT user_id FROM users WHERE is_banned = 0
            """)
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
