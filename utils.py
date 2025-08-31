"""
Utility functions for the Telegram bot
"""

import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict

logger = logging.getLogger(__name__)

class Utils:
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Format datetime for display"""
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def get_uptime(start_time: float) -> str:
        """Get formatted uptime"""
        uptime_seconds = time.time() - start_time
        uptime = timedelta(seconds=int(uptime_seconds))
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape markdown special characters"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    @staticmethod
    def parse_command_args(text: str) -> List[str]:
        """Parse command arguments from text"""
        parts = text.split()
        if len(parts) > 1:
            return parts[1:]
        return []
    
    @staticmethod
    def is_admin(user_id: int, admin_ids: List[int]) -> bool:
        """Check if user is admin"""
        return user_id in admin_ids
    
    @staticmethod
    def create_keyboard_markup(buttons: List[Dict]) -> str:
        """Create inline keyboard markup"""
        # This would be used with pyrogram's InlineKeyboardMarkup
        # For now, return a text representation
        keyboard_text = ""
        for row in buttons:
            for button in row:
                keyboard_text += f"[{button['text']}] "
            keyboard_text += "\n"
        return keyboard_text.strip()
    
    @staticmethod
    async def send_long_message(client, chat_id: int, text: str, max_length: int = 4096):
        """Send long message by splitting it"""
        if len(text) <= max_length:
            await client.send_message(chat_id, text)
            return
        
        # Split message into chunks
        chunks = []
        current_chunk = ""
        
        for line in text.split('\n'):
            if len(current_chunk + line + '\n') > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = line + '\n'
                else:
                    # Line itself is too long, split it
                    chunks.append(line[:max_length])
                    current_chunk = line[max_length:] + '\n'
            else:
                current_chunk += line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk)
        
        # Send chunks
        for i, chunk in enumerate(chunks):
            if i == 0:
                await client.send_message(chat_id, chunk)
            else:
                await client.send_message(chat_id, f"📄 **Continued...**\n\n{chunk}")
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Basic URL validation"""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        import re
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        return filename
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension"""
        import os
        return os.path.splitext(filename)[1].lower()
    
    @staticmethod
    def is_image_file(filename: str) -> bool:
        """Check if file is an image"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
        return Utils.get_file_extension(filename) in image_extensions
    
    @staticmethod
    def is_video_file(filename: str) -> bool:
        """Check if file is a video"""
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']
        return Utils.get_file_extension(filename) in video_extensions
    
    @staticmethod
    def is_audio_file(filename: str) -> bool:
        """Check if file is audio"""
        audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a']
        return Utils.get_file_extension(filename) in audio_extensions
    
    @staticmethod
    async def rate_limit(delay: float = 1.0):
        """Simple rate limiting"""
        await asyncio.sleep(delay)
    
    @staticmethod
    def generate_random_string(length: int = 10) -> str:
        """Generate random string"""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
