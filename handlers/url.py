"""
URL shortening command handlers
"""

import logging
from pyrogram import Client
from pyrogram.types import Message
from url_shortener import URLShortener
from utils import Utils

logger = logging.getLogger(__name__)

async def shorten_url(client: Client, message: Message, database):
    """Handle /short command - manually shorten URL"""
    try:
        args = Utils.parse_command_args(message.text)
        
        if not args:
            await message.reply(
                "🔗 **URL Shortener**\n\n"
                "Usage: `/short <url>`\n\n"
                "Example: `/short https://example.com/very/long/url`\n\n"
                "💡 **Tip:** You can also just send me a URL directly!"
            )
            return
        
        url = " ".join(args)
        
        # Add user to database
        user = message.from_user
        await database.add_user(
            user.id,
            user.username,
            user.first_name,
            user.last_name
        )
        
        # Get custom domain if set
        custom_domain = await database.get_setting("custom_domain") or ""
        
        # Initialize URL shortener
        shortener = URLShortener(database, custom_domain)
        
        # Show processing message
        processing_msg = await message.reply("🔗 **Shortening URL...**\n\n⏳ Please wait...")
        
        # Shorten the URL
        short_url = await shortener.shorten_url(user.id, url)
        
        if short_url:
            await processing_msg.edit_text(
                f"🎉 **URL Shortened Successfully!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌐 **Original URL:**\n"
                f"`{Utils.truncate_text(url, 45)}`\n\n"
                f"⚡ **Your Short Link:**\n"
                f"🔗 **{short_url}**\n\n"
                f"📈 **Features Enabled:**\n"
                f"• 📊 Real-time click tracking\n"
                f"• 🚀 Instant global access\n"
                f"• 📱 Mobile-optimized sharing\n"
                f"• 🔒 Secure & permanent\n\n"
                f"────────────────────────────\n"
                f"💫 **Powered by Mraprguild Tech**"
            )
        else:
            await processing_msg.edit_text(
                "❌ **Error shortening URL**\n\n"
                "Please check the URL format and try again.\n\n"
                "💡 **Valid format:** https://example.com"
            )
        
    except Exception as e:
        logger.error(f"Error in shorten URL command: {e}")
        await message.reply("❌ Error processing URL shortening request")

async def auto_shorten(client: Client, message: Message, database):
    """Automatically shorten URLs sent as messages"""
    try:
        url = message.text.strip()
        
        # Add user to database
        user = message.from_user
        await database.add_user(
            user.id,
            user.username,
            user.first_name,
            user.last_name
        )
        
        # Get custom domain if set
        custom_domain = await database.get_setting("custom_domain") or ""
        
        # Initialize URL shortener
        shortener = URLShortener(database, custom_domain)
        
        # Show processing message
        processing_msg = await message.reply("🔗 **Auto-shortening URL...**\n\n⏳ Processing...")
        
        # Shorten the URL
        short_url = await shortener.shorten_url(user.id, url)
        
        if short_url:
            await processing_msg.edit_text(
                f"⚡ **Auto-Magic URL Shortening!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🌍 **Original Link:**\n"
                f"`{Utils.truncate_text(url, 55)}`\n\n"
                f"🚀 **Your New Short URL:**\n"
                f"🔗 **{short_url}**\n\n"
                f"✨ **Smart Features Active:**\n"
                f"📊 Live analytics & click tracking\n"
                f"🌐 Custom domain: {'🟢 Active' if custom_domain else '🔴 Default'}\n"
                f"🔒 Permanent & secure link\n"
                f"📱 Mobile-friendly sharing\n\n"
                f"💡 **Pro Tip:** Use `/mystats` for detailed analytics!\n"
                f"────────────────────────────\n"
                f"🎯 **Mraprguild Auto-Shortener**"
            )
            
            # Log successful shortening
            logger.info(f"Auto-shortened URL for user {user.id}: {url} -> {short_url}")
        else:
            await processing_msg.edit_text(
                "❌ **Invalid URL Format**\n\n"
                "Please send a valid URL starting with http:// or https://\n\n"
                "✅ **Valid examples:**\n"
                "• https://example.com\n"
                "• http://subdomain.example.com/path\n"
                "• https://example.com/page?param=value"
            )
        
    except Exception as e:
        logger.error(f"Error in auto-shorten: {e}")
        await message.reply("❌ Error processing URL")

async def expand_url(client: Client, message: Message, database):
    """Handle URL expansion (for debugging/admin)"""
    try:
        args = Utils.parse_command_args(message.text)
        
        if not args:
            await message.reply(
                "🔍 **URL Expander**\n\n"
                "Usage: `/expand <short_code>`\n\n"
                "Example: `/expand abc123`\n\n"
                "This will show the original URL for a short code."
            )
            return
        
        short_code = args[0].strip()
        
        # Initialize URL shortener
        custom_domain = await database.get_setting("custom_domain") or ""
        shortener = URLShortener(database, custom_domain)
        
        # Expand the URL
        original_url = await shortener.expand_url(short_code)
        
        if original_url:
            # Get additional info
            cursor = await database.connection.execute("""
                SELECT 
                    s.original_url, s.click_count, s.created_date,
                    u.first_name, u.username
                FROM short_urls s
                LEFT JOIN users u ON s.user_id = u.user_id
                WHERE s.short_code = ?
            """, (short_code,))
            
            info = await cursor.fetchone()
            
            if info:
                creator = info[3] or "Unknown"
                username = f"@{info[4]}" if info[4] else ""
                created_date = info[2][:10] if info[2] else "Unknown"
                
                await message.reply(
                    f"🔍 **URL Information**\n\n"
                    f"📎 **Short Code:** {short_code}\n"
                    f"🔗 **Original URL:** {Utils.truncate_text(original_url, 100)}\n"
                    f"👆 **Clicks:** {info[1]}\n"
                    f"📅 **Created:** {created_date}\n"
                    f"👤 **Creator:** {creator} {username}\n\n"
                    f"✅ **Status:** Active"
                )
            else:
                await message.reply(f"🔗 **Original URL:** {original_url}")
        else:
            await message.reply(
                f"❌ **Short code not found:** {short_code}\n\n"
                "Please check the code and try again."
            )
        
    except Exception as e:
        logger.error(f"Error in expand URL command: {e}")
        await message.reply("❌ Error expanding URL")

async def my_urls(client: Client, message: Message, database):
    """Handle /myurls command - show user's URLs"""
    try:
        # Get user's URLs
        cursor = await database.connection.execute("""
            SELECT short_code, original_url, click_count, created_date
            FROM short_urls 
            WHERE user_id = ?
            ORDER BY created_date DESC
            LIMIT 10
        """, (message.from_user.id,))
        
        urls = await cursor.fetchall()
        
        if not urls:
            await message.reply(
                "🔗 **Your URLs**\n\n"
                "You haven't shortened any URLs yet.\n\n"
                "💡 **Get started:**\n"
                "• Send me any URL to shorten it\n"
                "• Use `/short <url>` command\n\n"
                "🚀 **Quick and easy!**"
            )
            return
        
        # Get custom domain
        custom_domain = await database.get_setting("custom_domain") or "https://short.ly"
        
        urls_text = f"🔗 **Your URLs** (Last 10)\n\n"
        
        for i, (short_code, original_url, click_count, created_date) in enumerate(urls, 1):
            short_url = f"{custom_domain}/{short_code}"
            date = created_date[:10] if created_date else "Unknown"
            
            urls_text += (
                f"**{i}. {Utils.truncate_text(original_url, 40)}**\n"
                f"📎 Short: {short_url}\n"
                f"👆 Clicks: {click_count}\n"
                f"📅 Created: {date}\n"
                f"🔑 Code: `{short_code}`\n\n"
            )
        
        urls_text += (
            f"📊 **Commands:**\n"
            f"• `/mystats` - View detailed statistics\n"
            f"• `/expand <code>` - Get URL info\n\n"
            f"💡 **Tip:** Share your short URLs anywhere!"
        )
        
        await Utils.send_long_message(client, message.chat.id, urls_text)
        
    except Exception as e:
        logger.error(f"Error in my_urls command: {e}")
        await message.reply("❌ Error retrieving your URLs")

async def delete_url(client: Client, message: Message, database, config):
    """Handle URL deletion"""
    try:
        args = Utils.parse_command_args(message.text)
        
        if not args:
            await message.reply(
                "🗑️ **Delete URL**\n\n"
                "Usage: `/deleteurl <short_code>`\n\n"
                "Example: `/deleteurl abc123`\n\n"
                "⚠️ **Warning:** This action cannot be undone!"
            )
            return
        
        short_code = args[0].strip()
        
        # Check if URL exists and user owns it (or is admin)
        cursor = await database.connection.execute("""
            SELECT user_id, original_url FROM short_urls WHERE short_code = ?
        """, (short_code,))
        
        url_info = await cursor.fetchone()
        
        if not url_info:
            await message.reply("❌ Short URL not found.")
            return
        
        # Check permissions
        if url_info[0] != message.from_user.id and not Utils.is_admin(message.from_user.id, config.ADMIN_IDS):
            await message.reply("❌ You can only delete your own URLs.")
            return
        
        # Delete the URL
        await database.connection.execute("""
            DELETE FROM short_urls WHERE short_code = ?
        """, (short_code,))
        await database.connection.commit()
        
        await message.reply(
            f"✅ **URL deleted successfully!**\n\n"
            f"🔑 **Code:** {short_code}\n"
            f"🔗 **URL:** {Utils.truncate_text(url_info[1], 50)}\n\n"
            f"🗑️ The short URL is no longer accessible."
        )
        
        logger.info(f"URL {short_code} deleted by user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error in delete URL command: {e}")
        await message.reply("❌ Error deleting URL")

async def url_stats(client: Client, message: Message, database):
    """Handle URL statistics"""
    try:
        args = Utils.parse_command_args(message.text)
        
        if not args:
            await message.reply(
                "📊 **URL Statistics**\n\n"
                "Usage: `/urlstats <short_code>`\n\n"
                "Example: `/urlstats abc123`\n\n"
                "This will show detailed statistics for your URL."
            )
            return
        
        short_code = args[0].strip()
        
        # Get URL info
        cursor = await database.connection.execute("""
            SELECT s.*, u.first_name, u.username
            FROM short_urls s
            LEFT JOIN users u ON s.user_id = u.user_id
            WHERE s.short_code = ?
        """, (short_code,))
        
        url_info = await cursor.fetchone()
        
        if not url_info:
            await message.reply("❌ Short URL not found.")
            return
        
        # Check if user owns the URL or is admin
        from config import Config
        config = Config()
        
        if url_info[1] != message.from_user.id and not Utils.is_admin(message.from_user.id, config.ADMIN_IDS):
            await message.reply("❌ You can only view statistics for your own URLs.")
            return
        
        # Get custom domain
        custom_domain = await database.get_setting("custom_domain") or "https://short.ly"
        short_url = f"{custom_domain}/{short_code}"
        
        creator = url_info[7] or "Unknown"
        username = f"@{url_info[8]}" if url_info[8] else ""
        created_date = url_info[5][:19] if url_info[5] else "Unknown"
        
        stats_text = (
            f"📊 **URL Statistics**\n\n"
            f"🔗 **URLs:**\n"
            f"• Short: {short_url}\n"
            f"• Original: {Utils.truncate_text(url_info[2], 60)}\n\n"
            
            f"📈 **Performance:**\n"
            f"• Total Clicks: {url_info[4]}\n"
            f"• Created: {created_date}\n"
            f"• Status: ✅ Active\n\n"
            
            f"👤 **Creator:**\n"
            f"• Name: {creator} {username}\n"
            f"• User ID: {url_info[1]}\n\n"
            
            f"⚙️ **Technical:**\n"
            f"• Short Code: `{short_code}`\n"
            f"• Custom Domain: {'✅' if url_info[3] else '❌'}\n"
        )
        
        await message.reply(stats_text)
        
    except Exception as e:
        logger.error(f"Error in URL stats command: {e}")
        await message.reply("❌ Error getting URL statistics")
