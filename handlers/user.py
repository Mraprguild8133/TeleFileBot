"""
User command handlers
"""

import logging
from pyrogram import Client
from pyrogram.types import Message
from utils import Utils

logger = logging.getLogger(__name__)

async def start_command(client: Client, message: Message, database):
    """Handle /start command"""
    try:
        user = message.from_user
        
        # Add user to database
        await database.add_user(
            user.id,
            user.username,
            user.first_name,
            user.last_name
        )
        
        welcome_text = (
            f"🚀 **Welcome to Mraprguild Bot!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👋 Hello **{user.first_name}**! Welcome to the future of file sharing!\n\n"
            
            f"✨ **What Makes Us Special?**\n"
            f"🔗 **Smart URL Shortening** • Custom domains supported\n"
            f"📁 **Massive File Support** • Up to 4GB with progress tracking\n"
            f"⚡ **Lightning Fast** • Instant processing & Telegram backup\n"
            f"🛡️ **Enterprise Security** • Your data, protected & private\n\n"
            
            f"🎯 **Quick Commands:**\n"
            f"▶️ `/help` - Complete feature guide\n"
            f"▶️ `/short <url>` - Create short links\n"
            f"▶️ `/myfiles` - Manage your files\n"
            f"▶️ `/mystats` - Track your usage\n\n"
            
            f"💎 **Pro Tips:**\n"
            f"🎪 **Just paste any URL** → Instant shortening!\n"
            f"🎪 **Drag & drop files** → Secure cloud storage!\n"
            f"🎪 **Everything backed up** → Never lose data again!\n\n"
            
            f"────────────────────────────\n"
            f"👨‍💻 **Crafted by:** Mraprguild\n"
            f"🔐 **100% Secure & Private**"
        )
        
        await message.reply(welcome_text)
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.reply("❌ Error processing start command")

async def help_command(client: Client, message: Message):
    """Handle /help command"""
    try:
        help_text = (
            f"📖 **Help - Mraprguild Bot**\n\n"
            
            f"🔗 **URL Shortening:**\n"
            f"• Send any URL to auto-shorten it\n"
            f"• Use `/short <url>` to manually shorten\n"
            f"• Custom domains supported\n"
            f"• Click tracking included\n\n"
            
            f"📁 **File Handling:**\n"
            f"• Send files up to 4GB\n"
            f"• Automatic backup to Telegram\n"
            f"• Local storage with file management\n"
            f"• Support for all file types\n\n"
            
            f"👤 **User Commands:**\n"
            f"• `/start` - Start the bot\n"
            f"• `/help` - Show this help\n"
            f"• `/short <url>` - Shorten URL\n"
            f"• `/myfiles` - View your files\n"
            f"• `/mystats` - Your statistics\n\n"
            
            f"👨‍💼 **Admin Commands:** (Admins only)\n"
            f"• `/status` - Bot status\n"
            f"• `/stats` - Detailed statistics\n"
            f"• `/broadcast` - Send broadcast message\n"
            f"• `/setdomain` - Set custom domain\n"
            f"• `/setapi` - Set API key\n\n"
            
            f"🔧 **Features:**\n"
            f"• Cross-platform support\n"
            f"• 4GB file limit\n"
            f"• Custom domain support\n"
            f"• Progress tracking\n"
            f"• Secure storage\n"
            f"• Fast processing\n\n"
            
            f"📞 **Support:**\n"
            f"Contact @Mraprguild for support\n\n"
            
            f"🔒 **Privacy:**\n"
            f"Your files and URLs are stored securely.\n"
            f"No data is shared with third parties."
        )
        
        await message.reply(help_text)
        
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await message.reply("❌ Error showing help")

async def my_files_command(client: Client, message: Message, database):
    """Handle /myfiles command - show user's files"""
    try:
        user_files = await database.get_user_files(message.from_user.id, 10)
        
        if not user_files:
            await message.reply(
                f"📁 **Your File Library**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🔍 **No files found**\n\n"
                f"💡 **Get Started:**\n"
                f"• Send any file to upload it\n"
                f"• Maximum size: 4GB\n"
                f"• All file types supported\n"
                f"• Automatic cloud backup\n\n"
                f"────────────────────────────\n"
                f"📂 **Mraprguild File Manager**"
            )
            return
        
        files_text = (
            f"📁 **Your File Library**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        
        for i, file_info in enumerate(user_files, 1):
            file_size = Utils.format_file_size(file_info['file_size'])
            upload_date = file_info['upload_date'][:10]  # Just the date part
            name_short = file_info['file_name'][:25] + "..." if len(file_info['file_name']) > 25 else file_info['file_name']
            
            type_icon = {
                'image': '🖼️',
                'video': '🎥',
                'audio': '🎵',
                'document': '📄',
                'archive': '📦'
            }.get(file_info['file_type'], '📎')
            
            files_text += (
                f"**{i}. {type_icon} {name_short}**\n"
                f"▶️ Size: {file_size}\n"
                f"▶️ Type: {file_info['file_type'].title()}\n"
                f"▶️ Date: {upload_date}\n"
                f"▶️ ID: `{file_info['file_id']}`\n\n"
            )
        
        files_text += (
            f"🎯 **File Actions:**\n"
            f"• `/forward <file_id> <chat_id>` - Forward file\n"
            f"• Use file ID to reference files\n\n"
            f"────────────────────────────\n"
            f"📂 **Mraprguild File Manager**"
        )
        
        await Utils.send_long_message(client, message.chat.id, files_text)
        
    except Exception as e:
        logger.error(f"Error in my_files command: {e}")
        await message.reply("❌ Error retrieving your files")

async def my_stats_command(client: Client, message: Message, database):
    """Handle /mystats command - show user statistics"""
    try:
        user_info = await database.get_user(message.from_user.id)
        
        if not user_info:
            await message.reply("❌ User not found")
            return
        
        # Get detailed stats
        cursor = await database.connection.execute("""
            SELECT COUNT(*), SUM(click_count) 
            FROM short_urls WHERE user_id = ?
        """, (message.from_user.id,))
        
        url_stats = await cursor.fetchone()
        total_urls = url_stats[0] if url_stats[0] else 0
        total_clicks = url_stats[1] if url_stats[1] else 0
        
        cursor = await database.connection.execute("""
            SELECT COUNT(*), SUM(file_size) 
            FROM files WHERE user_id = ?
        """, (message.from_user.id,))
        
        file_stats = await cursor.fetchone()
        total_files = file_stats[0] if file_stats[0] else 0
        total_size = file_stats[1] if file_stats[1] else 0
        
        join_date = user_info['join_date'][:10]  # Just the date part
        
        stats_text = (
            f"📊 **Your Statistics**\n\n"
            f"👤 **Profile:**\n"
            f"• Name: {user_info['first_name']}\n"
            f"• Username: @{user_info['username'] or 'Not set'}\n"
            f"• Join Date: {join_date}\n\n"
            
            f"🔗 **URL Shortening:**\n"
            f"• URLs Created: {total_urls}\n"
            f"• Total Clicks: {total_clicks}\n"
            f"• Average Clicks: {total_clicks / max(total_urls, 1):.1f}\n\n"
            
            f"📁 **File Storage:**\n"
            f"• Files Uploaded: {total_files}\n"
            f"• Total Size: {Utils.format_file_size(total_size)}\n"
            f"• Average Size: {Utils.format_file_size(total_size / max(total_files, 1))}\n\n"
            
            f"🏆 **Achievements:**\n"
        )
        
        # Add achievements
        if total_urls >= 100:
            stats_text += "🔗 URL Master (100+ URLs)\n"
        elif total_urls >= 50:
            stats_text += "🔗 URL Expert (50+ URLs)\n"
        elif total_urls >= 10:
            stats_text += "🔗 URL Enthusiast (10+ URLs)\n"
        
        if total_files >= 50:
            stats_text += "📁 File Master (50+ Files)\n"
        elif total_files >= 20:
            stats_text += "📁 File Expert (20+ Files)\n"
        elif total_files >= 5:
            stats_text += "📁 File Enthusiast (5+ Files)\n"
        
        if total_clicks >= 1000:
            stats_text += "👆 Click Master (1000+ Clicks)\n"
        elif total_clicks >= 100:
            stats_text += "👆 Click Expert (100+ Clicks)\n"
        
        await message.reply(stats_text)
        
    except Exception as e:
        logger.error(f"Error in my_stats command: {e}")
        await message.reply("❌ Error retrieving your statistics")

async def forward_file_command(client: Client, message: Message, database):
    """Handle /forward command - forward file to another chat"""
    try:
        args = Utils.parse_command_args(message.text)
        
        if len(args) < 2:
            await message.reply(
                f"📤 **File Forwarding System**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⚙️ **Usage:**\n"
                f"• `/forward <file_id> <chat_id>`\n"
                f"• `/forward <file_id> @username`\n\n"
                f"📋 **Examples:**\n"
                f"• `/forward abc123 -1001234567890`\n"
                f"• `/forward abc123 @mraprguild`\n\n"
                f"💡 **Tips:**\n"
                f"• Use `/myfiles` to get file IDs\n"
                f"• Chat ID can be user or group\n"
                f"• Files forwarded instantly\n\n"
                f"────────────────────────────\n"
                f"🚀 **Mraprguild File Forwarder**"
            )
            return
        
        file_id = args[0].strip()
        target_chat = args[1].strip()
        user_id = message.from_user.id
        
        # Get file info
        cursor = await database.connection.execute("""
            SELECT file_name, file_path, telegram_message_id
            FROM files 
            WHERE file_id = ? AND user_id = ?
        """, (file_id, user_id))
        
        file_info = await cursor.fetchone()
        
        if not file_info:
            await message.reply(
                f"❌ **File Not Found**\n\n"
                f"🔍 File ID `{file_id}` not found in your library.\n\n"
                f"💡 Use `/myfiles` to see your files."
            )
            return
        
        file_name, file_path, telegram_message_id = file_info
        
        # Show processing message
        processing_msg = await message.reply(
            f"📤 **Forwarding File...**\n\n"
            f"📁 **File:** {file_name[:30]}...\n"
            f"🎯 **Target:** {target_chat}\n\n"
            f"⏳ **Processing...**"
        )
        
        try:
            # Forward the file
            storage_channel_id = await database.get_setting("storage_channel_id")
            if storage_channel_id and telegram_message_id:
                forwarded = await client.forward_messages(
                    chat_id=target_chat,
                    from_chat_id=int(storage_channel_id),
                    message_ids=[int(telegram_message_id)]
                )
                
                await processing_msg.edit_text(
                    f"✅ **File Forwarded Successfully!**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📁 **File:** {file_name[:30]}...\n"
                    f"🎯 **Sent To:** {target_chat}\n"
                    f"📤 **Status:** ✅ Delivered\n\n"
                    f"🚀 **Features:**\n"
                    f"• Instant delivery\n"
                    f"• Original quality preserved\n"
                    f"• Metadata maintained\n\n"
                    f"────────────────────────────\n"
                    f"📤 **Mraprguild File Forwarder**"
                )
            else:
                await processing_msg.edit_text(
                    f"❌ **Forward Failed**\n\n"
                    f"File not available for forwarding.\n\n"
                    f"💡 Storage channel not configured."
                )
            
        except Exception as forward_error:
            await processing_msg.edit_text(
                f"❌ **Forward Failed**\n\n"
                f"Error: {str(forward_error)[:50]}...\n\n"
                f"💡 **Common Issues:**\n"
                f"• Invalid chat ID\n"
                f"• Bot not in target chat\n"
                f"• Insufficient permissions\n\n"
                f"🔧 **Try Again:** Check chat ID and permissions"
            )
        
    except Exception as e:
        logger.error(f"Error in forward file command: {e}")
        await message.reply("❌ Error forwarding file")

async def default_message(client: Client, message: Message):
    """Handle non-command messages"""
    try:
        if message.text:
            # Check if it's a URL
            if Utils.validate_url(message.text):
                # This will be handled by the URL shortener
                return
            
            # Default response for other text
            await message.reply(
                "🤔 **I didn't understand that.**\n\n"
                "💡 **What you can do:**\n"
                "• Send me a URL to shorten it\n"
                "• Send me a file to store it\n"
                "• Use `/help` for more information\n\n"
                "👨‍💻 **Made by Mraprguild**"
            )
    
    except Exception as e:
        logger.error(f"Error in default message handler: {e}")
