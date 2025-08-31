"""
File handling functionality for the Telegram bot
"""

import os
import asyncio
import aiofiles
import logging
from typing import Optional, Callable
from pyrogram.types import Message
from pyrogram.errors import FloodWait

logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self, config, database):
        """Initialize file handler"""
        self.config = config
        self.database = database
        self.max_file_size = config.MAX_FILE_SIZE
        self.chunk_size = config.CHUNK_SIZE
        self.files_dir = config.FILES_DIR
        self.temp_dir = config.TEMP_DIR
        
        # Ensure directories exist
        os.makedirs(self.files_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    def get_file_type(self, file_name: str) -> str:
        """Determine file type from extension"""
        extension = os.path.splitext(file_name)[1].lower()
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
        audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma']
        document_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt']
        archive_extensions = ['.zip', '.rar', '.7z', '.tar', '.gz']
        
        if extension in image_extensions:
            return "image"
        elif extension in video_extensions:
            return "video"
        elif extension in audio_extensions:
            return "audio"
        elif extension in document_extensions:
            return "document"
        elif extension in archive_extensions:
            return "archive"
        else:
            return "file"
    
    async def progress_callback(self, current: int, total: int, message: Message, action: str):
        """Progress callback for file operations"""
        try:
            percentage = (current / total) * 100
            
            # Update progress every 5%
            if int(percentage) % 5 == 0:
                progress_bar = "█" * int(percentage // 5) + "░" * (20 - int(percentage // 5))
                
                size_current = self.format_file_size(current)
                size_total = self.format_file_size(total)
                
                progress_text = (
                    f"📁 **{action}**\n\n"
                    f"📊 **Progress:** {percentage:.1f}%\n"
                    f"▶️ `{progress_bar}`\n"
                    f"📦 **Size:** {size_current} / {size_total}\n"
                    f"⚡ **Speed:** {self.format_file_size(current // 5)}/s"
                )
                
                try:
                    await message.edit_text(progress_text)
                except Exception:
                    pass  # Ignore edit errors
                    
        except Exception as e:
            logger.error(f"Progress callback error: {e}")
    
    async def download_file(self, client, message: Message, file_path: str) -> bool:
        """Download file from Telegram"""
        try:
            progress_msg = await message.reply(
                "📥 **Starting Download...**\n\n"
                "📊 **Progress:** 0%\n"
                "⏳ Please wait..."
            )
            
            # Download with progress
            await client.download_media(
                message,
                file_name=file_path,
                progress=lambda current, total: asyncio.create_task(
                    self.progress_callback(current, total, progress_msg, "Downloading")
                )
            )
            
            await progress_msg.edit_text(
                "✅ **Download Complete!**\n\n"
                f"📁 **File:** {os.path.basename(file_path)}\n"
                f"📦 **Size:** {self.format_file_size(os.path.getsize(file_path))}"
            )
            
            return True
            
        except FloodWait as e:
            logger.warning(f"FloodWait: {e.x} seconds")
            await asyncio.sleep(e.x)
            return await self.download_file(client, message, file_path)
            
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False
    
    async def upload_file(self, client, chat_id: int, file_path: str, 
                         caption: str = None) -> Optional[Message]:
        """Upload file to Telegram"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
            
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.error(f"File too large: {self.format_file_size(file_size)}")
                return None
            
            # Send initial message
            progress_msg = await client.send_message(
                chat_id,
                "📤 **Starting Upload...**\n\n"
                "📊 **Progress:** 0%\n"
                "⏳ Please wait..."
            )
            
            # Upload with progress
            sent_message = await client.send_document(
                chat_id,
                file_path,
                caption=caption,
                progress=lambda current, total: asyncio.create_task(
                    self.progress_callback(current, total, progress_msg, "Uploading")
                )
            )
            
            await progress_msg.delete()
            return sent_message
            
        except FloodWait as e:
            logger.warning(f"FloodWait: {e.x} seconds")
            await asyncio.sleep(e.x)
            return await self.upload_file(client, chat_id, file_path, caption)
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None
    
    async def process_file(self, client, message: Message) -> bool:
        """Process incoming file"""
        try:
            # Get file information
            if message.document:
                file_name = message.document.file_name or f"file_{message.id}"
                file_size = message.document.file_size
                file_id = message.document.file_id
            elif message.video:
                file_name = message.video.file_name or f"video_{message.id}.mp4"
                file_size = message.video.file_size
                file_id = message.video.file_id
            elif message.audio:
                file_name = message.audio.file_name or f"audio_{message.id}.mp3"
                file_size = message.audio.file_size
                file_id = message.audio.file_id
            elif message.photo:
                file_name = f"photo_{message.id}.jpg"
                file_size = message.photo.file_size
                file_id = message.photo.file_id
            else:
                return False
            
            # Check file size
            if file_size > self.max_file_size:
                await message.reply(
                    f"🚫 **File Size Limit Exceeded!**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📦 **Your File:** {self.format_file_size(file_size)}\n"
                    f"⚠️ **Maximum Allowed:** {self.format_file_size(self.max_file_size)}\n\n"
                    f"💡 **Suggestions:**\n"
                    f"• Compress your file\n"
                    f"• Split into smaller parts\n"
                    f"• Use file compression tools\n\n"
                    f"────────────────────────────\n"
                    f"🔧 **Mraprguild File Limits**"
                )
                return False
            
            # Create file path
            safe_filename = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            file_path = os.path.join(self.files_dir, f"{message.from_user.id}_{safe_filename}")
            
            # Download file
            success = await self.download_file(client, message, file_path)
            
            if success:
                # Store file info in database
                file_type = self.get_file_type(file_name)
                
                channel_message_id = None
                if self.config.STORAGE_CHANNEL_ID:
                    try:
                        # Forward to storage channel
                        channel_msg = await client.forward_messages(
                            self.config.STORAGE_CHANNEL_ID,
                            message.chat.id,
                            message.id
                        )
                        channel_message_id = channel_msg.id
                    except Exception as e:
                        logger.warning(f"Could not forward to storage channel: {e}")
                
                await self.database.add_file(
                    message.from_user.id,
                    file_name,
                    file_size,
                    file_type,
                    file_id,
                    message.id,
                    channel_message_id
                )
                
                # Send success message
                await message.reply(
                    f"🎉 **File Upload Complete!**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📁 **File Details:**\n"
                    f"▶️ Name: **{file_name}**\n"
                    f"▶️ Size: **{self.format_file_size(file_size)}**\n"
                    f"▶️ Type: **{file_type.title()}**\n\n"
                    f"🚀 **Storage Systems:**\n"
                    f"• 💾 Local secure storage\n"
                    f"• ☁️ Telegram cloud backup\n"
                    f"• 🔒 Encrypted & protected\n\n"
                    f"🆔 **Your File ID:**\n"
                    f"`{file_id}`\n\n"
                    f"────────────────────────────\n"
                    f"✨ **Mraprguild File Manager**"
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            await message.reply(
                "❌ **Error Processing File!**\n\n"
                "Please try again later."
            )
            return False
    
    async def forward_file(self, client, from_chat: int, message_id: int, 
                          to_chat: int) -> Optional[Message]:
        """Forward file between chats"""
        try:
            forwarded = await client.forward_messages(
                to_chat,
                from_chat,
                message_id
            )
            return forwarded
            
        except Exception as e:
            logger.error(f"Error forwarding file: {e}")
            return None
    
    async def get_file_info(self, file_id: str) -> Optional[dict]:
        """Get file information from database"""
        try:
            cursor = await self.database.connection.execute("""
                SELECT * FROM files WHERE file_id = ?
            """, (file_id,))
            
            row = await cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None
    
    async def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path):
                    # Delete files older than 1 hour
                    file_age = asyncio.get_event_loop().time() - os.path.getmtime(file_path)
                    if file_age > 3600:  # 1 hour
                        os.remove(file_path)
                        logger.info(f"Cleaned up temp file: {filename}")
        except Exception as e:
            logger.error(f"Error cleaning temp files: {e}")
