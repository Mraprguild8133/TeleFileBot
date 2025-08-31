"""
Main Telegram Bot Class
"""

import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database import Database
from handlers import admin, user, file, url

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        """Initialize the Telegram bot"""
        self.config = Config()
        self.database = Database()
        
        # Initialize Pyrogram client
        self.app = Client(
            "mraprguild_bot",
            api_id=self.config.API_ID,
            api_hash=self.config.API_HASH,
            bot_token=self.config.BOT_TOKEN,
            workdir="./session"
        )
        
        # Register handlers
        self._register_handlers()
        
    def _register_handlers(self):
        """Register all bot handlers"""
        
        # Admin handlers
        @self.app.on_message(filters.command("start"))
        async def start_handler(client, message):
            await user.start_command(client, message, self.database)
            
        @self.app.on_message(filters.command("help"))
        async def help_handler(client, message):
            await user.help_command(client, message)
            
        @self.app.on_message(filters.command("status") & filters.user(self.config.ADMIN_IDS))
        async def status_handler(client, message):
            await admin.status_command(client, message, self.database)
            
        @self.app.on_message(filters.command("stats") & filters.user(self.config.ADMIN_IDS))
        async def stats_handler(client, message):
            await admin.stats_command(client, message, self.database)
            
        @self.app.on_message(filters.command("broadcast") & filters.user(self.config.ADMIN_IDS))
        async def broadcast_handler(client, message):
            await admin.broadcast_command(client, message, self.database)
            
        # URL shortening handlers
        @self.app.on_message(filters.command("short"))
        async def short_url_handler(client, message):
            await url.shorten_url(client, message, self.database)
            
        @self.app.on_message(filters.regex(r"^https?://"))
        async def auto_short_handler(client, message):
            await url.auto_shorten(client, message, self.database)
            
        # File handling handlers
        @self.app.on_message(filters.document | filters.video | filters.audio | filters.photo)
        async def file_handler(client, message):
            await file.handle_file(client, message, self.database, self.config)
            
        @self.app.on_message(filters.command("forward"))
        async def forward_handler(client, message):
            await user.forward_file_command(client, message, self.database)
            
        @self.app.on_message(filters.command("myfiles"))
        async def myfiles_handler(client, message):
            await user.my_files_command(client, message, self.database)
            
        @self.app.on_message(filters.command("mystats"))
        async def mystats_handler(client, message):
            await user.my_stats_command(client, message, self.database)
            
        # Custom domain handlers
        @self.app.on_message(filters.command("setdomain") & filters.user(self.config.ADMIN_IDS))
        async def set_domain_handler(client, message):
            await admin.set_custom_domain(client, message, self.database)
            
        @self.app.on_message(filters.command("setapi") & filters.user(self.config.ADMIN_IDS))
        async def set_api_handler(client, message):
            await admin.set_api_key(client, message, self.database)
            
        # Error handler
        @self.app.on_message()
        async def default_handler(client, message):
            if message.text and not message.text.startswith('/'):
                await user.default_message(client, message)
    
    async def start(self):
        """Start the bot"""
        try:
            # Initialize database
            await self.database.initialize()
            
            # Start Pyrogram client
            await self.app.start()
            
            # Send startup notification to owner
            try:
                await self.app.send_message(
                    self.config.OWNER_ID,
                    "🤖 **Bot Started Successfully!**\n\n"
                    f"👨‍💻 **Owner:** Mraprguild\n"
                    f"🆔 **Bot ID:** @{(await self.app.get_me()).username}\n"
                    f"📊 **Status:** Online\n"
                    f"💾 **Database:** Connected\n"
                    f"🔗 **URL Shortener:** Ready\n"
                    f"📁 **File Handler:** Ready (4GB limit)"
                )
            except Exception as e:
                logger.warning(f"Could not send startup notification: {e}")
                
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
    
    async def idle(self):
        """Keep the bot running"""
        import asyncio
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
    
    async def stop(self):
        """Stop the bot"""
        try:
            await self.app.stop()
            await self.database.close()
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
