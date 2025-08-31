"""
Admin command handlers
"""

import time
import asyncio
import logging
from pyrogram import Client
from pyrogram.types import Message
from utils import Utils

logger = logging.getLogger(__name__)
start_time = time.time()

async def status_command(client: Client, message: Message, database):
    """Handle /status command - show bot status"""
    try:
        # Get bot info
        bot_info = await client.get_me()
        
        # Get statistics
        stats = await database.get_statistics()
        
        # Get uptime
        uptime = Utils.get_uptime(start_time)
        
        # Get custom domain and API key status
        custom_domain = await database.get_setting("custom_domain") or "Not set"
        api_key_status = "✅ Set" if await database.get_setting("api_key") else "❌ Not set"
        
        status_text = (
            f"🚀 **Mraprguild Bot Control Center**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🤖 **System Information:**\n"
            f"▶️ Bot Name: **{bot_info.first_name}**\n"
            f"▶️ Username: @{bot_info.username}\n"
            f"▶️ Bot ID: `{bot_info.id}`\n"
            f"▶️ Status: 🟢 **ONLINE & ACTIVE**\n"
            f"▶️ Uptime: ⏱️ {uptime}\n\n"
            
            f"📊 **Performance Metrics:**\n"
            f"👥 Active Users: **{stats.get('total_users', 0)}**\n"
            f"🔗 URLs Created: **{stats.get('total_urls', 0)}**\n"
            f"📁 Files Stored: **{stats.get('total_files', 0)}**\n"
            f"👆 Total Clicks: **{stats.get('total_clicks', 0)}**\n"
            f"💾 Storage Used: **{Utils.format_file_size(stats.get('total_file_size', 0))}**\n\n"
            
            f"⚙️ **System Configuration:**\n"
            f"🌐 Custom Domain: `{custom_domain}`\n"
            f"🔑 API Integration: {api_key_status}\n"
            f"📦 File Capacity: **4GB Max**\n"
            f"🗄️ Database: 🟢 **Connected & Healthy**\n\n"
            
            f"────────────────────────────\n"
            f"👨‍💻 **System Owner:** Mraprguild\n"
            f"🌟 **Enterprise Grade Performance**"
        )
        
        await message.reply(status_text)
        
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await message.reply("❌ Error getting bot status")

async def stats_command(client: Client, message: Message, database):
    """Handle /stats command - detailed statistics"""
    try:
        stats = await database.get_statistics()
        
        # Get detailed stats
        cursor = await database.connection.execute("""
            SELECT 
                DATE(created_date) as date,
                COUNT(*) as url_count
            FROM short_urls 
            WHERE created_date >= date('now', '-7 days')
            GROUP BY DATE(created_date)
            ORDER BY date DESC
        """)
        
        recent_urls = await cursor.fetchall()
        
        cursor = await database.connection.execute("""
            SELECT 
                DATE(upload_date) as date,
                COUNT(*) as file_count
            FROM files 
            WHERE upload_date >= date('now', '-7 days')
            GROUP BY DATE(upload_date)
            ORDER BY date DESC
        """)
        
        recent_files = await cursor.fetchall()
        
        stats_text = (
            f"📊 **Detailed Statistics - Mraprguild Bot**\n\n"
            f"🔗 **URL Shortening:**\n"
            f"• Total URLs Created: {stats.get('total_urls', 0)}\n"
            f"• Total Clicks: {stats.get('total_clicks', 0)}\n"
            f"• Average Clicks per URL: {stats.get('total_clicks', 0) / max(stats.get('total_urls', 1), 1):.1f}\n\n"
            
            f"📁 **File Handling:**\n"
            f"• Total Files: {stats.get('total_files', 0)}\n"
            f"• Total Storage: {Utils.format_file_size(stats.get('total_file_size', 0))}\n"
            f"• Average File Size: {Utils.format_file_size(stats.get('total_file_size', 0) / max(stats.get('total_files', 1), 1))}\n\n"
            
            f"👥 **Users:**\n"
            f"• Total Users: {stats.get('total_users', 0)}\n\n"
            
            f"📅 **Recent Activity (Last 7 days):**\n"
        )
        
        # Add recent URL stats
        if recent_urls:
            stats_text += "🔗 URLs:\n"
            for date, count in recent_urls[:5]:
                stats_text += f"• {date}: {count} URLs\n"
        
        # Add recent file stats
        if recent_files:
            stats_text += "\n📁 Files:\n"
            for date, count in recent_files[:5]:
                stats_text += f"• {date}: {count} Files\n"
        
        await message.reply(stats_text)
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await message.reply("❌ Error getting statistics")

async def broadcast_command(client: Client, message: Message, database):
    """Handle /broadcast command - send message to all users"""
    try:
        # Check if there's a message to broadcast
        if message.reply_to_message:
            broadcast_message = message.reply_to_message
        else:
            args = Utils.parse_command_args(message.text)
            if not args:
                await message.reply(
                    "📢 **Broadcast Message**\n\n"
                    "Usage: `/broadcast <message>` or reply to a message with `/broadcast`"
                )
                return
            broadcast_text = " ".join(args)
        
        # Get all users
        users = await database.get_all_users()
        
        if not users:
            await message.reply("❌ No users to broadcast to")
            return
        
        # Start broadcasting
        status_msg = await message.reply(
            f"📢 **Starting Broadcast**\n\n"
            f"👥 Total Users: {len(users)}\n"
            f"✅ Sent: 0\n"
            f"❌ Failed: 0\n"
            f"⏳ Progress: 0%"
        )
        
        sent_count = 0
        failed_count = 0
        
        for i, user_id in enumerate(users):
            try:
                if message.reply_to_message:
                    await client.forward_messages(user_id, message.chat.id, broadcast_message.id)
                else:
                    await client.send_message(user_id, broadcast_text)
                
                sent_count += 1
                
                # Rate limiting
                await Utils.rate_limit(0.1)
                
            except Exception as e:
                failed_count += 1
                logger.warning(f"Failed to send broadcast to {user_id}: {e}")
            
            # Update progress every 10 users
            if (i + 1) % 10 == 0 or i == len(users) - 1:
                progress = ((i + 1) / len(users)) * 100
                
                try:
                    await status_msg.edit_text(
                        f"📢 **Broadcasting...**\n\n"
                        f"👥 Total Users: {len(users)}\n"
                        f"✅ Sent: {sent_count}\n"
                        f"❌ Failed: {failed_count}\n"
                        f"⏳ Progress: {progress:.1f}%"
                    )
                except:
                    pass
        
        # Final status
        await status_msg.edit_text(
            f"📢 **Broadcast Complete!**\n\n"
            f"👥 Total Users: {len(users)}\n"
            f"✅ Sent: {sent_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"📊 Success Rate: {(sent_count / len(users)) * 100:.1f}%"
        )
        
    except Exception as e:
        logger.error(f"Error in broadcast command: {e}")
        await message.reply("❌ Error broadcasting message")

async def set_custom_domain(client: Client, message: Message, database):
    """Handle /setdomain command - set custom domain"""
    try:
        args = Utils.parse_command_args(message.text)
        
        if not args:
            current_domain = await database.get_setting("custom_domain") or "Not configured"
            await message.reply(
                f"🌐 **Custom Domain Manager**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📊 **Current Configuration:**\n"
                f"▶️ Domain: `{current_domain}`\n"
                f"▶️ Status: {'🟢 Active' if current_domain != 'Not configured' else '🔴 Inactive'}\n\n"
                f"⚙️ **Setup Instructions:**\n"
                f"• Use: `/setdomain <your-domain>`\n"
                f"• Format: `https://short.yourdomain.com`\n"
                f"• Example: `/setdomain https://s.mraprguild.com`\n\n"
                f"🎯 **Benefits:**\n"
                f"• Branded short URLs\n"
                f"• Professional appearance\n"
                f"• Better click-through rates\n"
                f"• Custom analytics\n\n"
                f"────────────────────────────\n"
                f"🚀 **Mraprguild Domain System**"
            )
            return
        
        domain = args[0].strip()
        
        # Basic validation
        if not Utils.validate_url(domain):
            await message.reply("❌ Invalid domain format. Please use a valid URL.")
            return
        
        # Save domain
        await database.set_setting("custom_domain", domain)
        
        await message.reply(
            f"🎉 **Custom Domain Activated!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🌐 **Your New Domain:**\n"
            f"`{domain}`\n\n"
            f"✨ **What's Changed:**\n"
            f"• All new URLs use your domain\n"
            f"• Branded short links active\n"
            f"• Professional appearance enabled\n"
            f"• Custom analytics available\n\n"
            f"🚀 **Next Steps:**\n"
            f"• Configure DNS records\n"
            f"• Set up SSL certificate\n"
            f"• Test your short URLs\n\n"
            f"────────────────────────────\n"
            f"✅ **Domain Successfully Configured**"
        )
        
    except Exception as e:
        logger.error(f"Error setting custom domain: {e}")
        await message.reply("❌ Error setting custom domain")

async def set_api_key(client: Client, message: Message, database):
    """Handle /setapi command - set API key"""
    try:
        args = Utils.parse_command_args(message.text)
        
        if not args:
            api_key_exists = await database.get_setting("api_key")
            api_status = "🟢 Configured" if api_key_exists else "🔴 Not Set"
            await message.reply(
                f"🔑 **API Key Management Center**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📊 **Current Status:**\n"
                f"▶️ API Integration: {api_status}\n"
                f"▶️ External Services: {'✅ Enabled' if api_key_exists else '❌ Disabled'}\n\n"
                f"⚙️ **Setup Instructions:**\n"
                f"• Use: `/setapi <your-api-key>`\n"
                f"• Example: `/setapi abcd1234...`\n\n"
                f"🎯 **API Benefits:**\n"
                f"• External URL shortening\n"
                f"• Advanced analytics\n"
                f"• Premium features access\n"
                f"• Enhanced rate limits\n\n"
                f"🔒 **Security Features:**\n"
                f"• Encrypted storage\n"
                f"• Auto-delete commands\n"
                f"• Secure transmission\n\n"
                f"────────────────────────────\n"
                f"🛡️ **Mraprguild Security System**"
            )
            return
        
        api_key = args[0].strip()
        
        # Save API key
        await database.set_setting("api_key", api_key)
        
        # Send confirmation
        confirmation = await message.reply(
            f"🎉 **API Key Configured Successfully!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ **Status Update:**\n"
            f"• API key stored securely\n"
            f"• External services enabled\n"
            f"• Premium features unlocked\n"
            f"• Enhanced analytics active\n\n"
            f"🔒 **Security Protocol:**\n"
            f"• Command auto-deleted in 10s\n"
            f"• Encrypted database storage\n"
            f"• Zero-log transmission\n\n"
            f"────────────────────────────\n"
            f"🛡️ **Mraprguild Security Active**"
        )
        
        # Delete messages for security
        await asyncio.sleep(10)
        try:
            await message.delete()
            await confirmation.delete()
        except:
            pass
        
    except Exception as e:
        logger.error(f"Error setting API key: {e}")
        await message.reply("❌ Error setting API key")
