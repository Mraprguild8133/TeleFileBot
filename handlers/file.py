"""
File handling command handlers
"""

import logging
from pyrogram import Client
from pyrogram.types import Message
from file_handler import FileHandler
from utils import Utils

logger = logging.getLogger(__name__)

async def handle_file(client: Client, message: Message, database, config):
    """Handle incoming file uploads"""
    try:
        # Initialize file handler
        file_handler = FileHandler(config, database)
        
        # Add user to database
        user = message.from_user
        await database.add_user(
            user.id,
            user.username,
            user.first_name,
            user.last_name
        )
        
        # Process the file
        success = await file_handler.process_file(client, message)
        
        if success:
            logger.info(f"File processed successfully for user {user.id}")
        else:
            logger.warning(f"File processing failed for user {user.id}")
            
    except Exception as e:
        logger.error(f"Error handling file: {e}")
        await message.reply(
            "❌ **Error processing file**\n\n"
            "Please try again later or contact support."
        )

async def forward_file(client: Client, message: Message, database, config):
    """Handle /forward command - forward file to another chat"""
    try:
        args = Utils.parse_command_args(message.text)
        
        if len(args) < 2:
            await message.reply(
                "📤 **Forward File**\n\n"
                "Usage: `/forward <file_id> <chat_id>`\n\n"
                "• Get file_id from `/myfiles` command\n"
                "• chat_id is the destination chat/channel ID\n\n"
                "Example: `/forward ABC123 -1001234567890`"
            )
            return
        
        file_id = args[0]
        try:
            chat_id = int(args[1])
        except ValueError:
            await message.reply("❌ Invalid chat ID. Please use a numeric chat ID.")
            return
        
        # Check if user owns the file or is admin
        if not Utils.is_admin(message.from_user.id, config.ADMIN_IDS):
            cursor = await database.connection.execute("""
                SELECT * FROM files WHERE file_id = ? AND user_id = ?
            """, (file_id, message.from_user.id))
            
            file_info = await cursor.fetchone()
            if not file_info:
                await message.reply("❌ File not found or you don't have permission to forward it.")
                return
        else:
            # Admin can forward any file
            cursor = await database.connection.execute("""
                SELECT * FROM files WHERE file_id = ?
            """, (file_id,))
            
            file_info = await cursor.fetchone()
            if not file_info:
                await message.reply("❌ File not found.")
                return
        
        # Initialize file handler
        file_handler = FileHandler(config, database)
        
        # Forward the file
        try:
            # Get original message info
            original_chat = file_info[1]  # user_id
            original_message_id = file_info[6]  # message_id
            
            forwarded = await file_handler.forward_file(
                client, original_chat, original_message_id, chat_id
            )
            
            if forwarded:
                await message.reply(
                    f"✅ **File forwarded successfully!**\n\n"
                    f"📁 **File:** {file_info[2]}\n"  # file_name
                    f"📤 **To:** {chat_id}\n"
                    f"🆔 **Message ID:** {forwarded.id}"
                )
            else:
                await message.reply("❌ Failed to forward file. Check chat ID and permissions.")
                
        except Exception as e:
            logger.error(f"Error forwarding file: {e}")
            await message.reply(f"❌ Error forwarding file: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error in forward command: {e}")
        await message.reply("❌ Error processing forward command")

async def download_file(client: Client, message: Message, database, config):
    """Handle file download requests"""
    try:
        args = Utils.parse_command_args(message.text)
        
        if not args:
            await message.reply(
                "📥 **Download File**\n\n"
                "Usage: `/download <file_id>`\n\n"
                "• Get file_id from `/myfiles` command\n\n"
                "Example: `/download ABC123`"
            )
            return
        
        file_id = args[0]
        
        # Get file info
        cursor = await database.connection.execute("""
            SELECT * FROM files WHERE file_id = ?
        """, (file_id,))
        
        file_info = await cursor.fetchone()
        
        if not file_info:
            await message.reply("❌ File not found.")
            return
        
        # Check if user owns the file or is admin
        if not Utils.is_admin(message.from_user.id, config.ADMIN_IDS) and file_info[1] != message.from_user.id:
            await message.reply("❌ You don't have permission to download this file.")
            return
        
        try:
            # Send file info first
            file_size = Utils.format_file_size(file_info[3])
            
            info_text = (
                f"📁 **File Information**\n\n"
                f"**Name:** {file_info[2]}\n"
                f"**Size:** {file_size}\n"
                f"**Type:** {file_info[4].title()}\n"
                f"**Upload Date:** {file_info[7][:10]}\n\n"
                f"📤 **Sending file...**"
            )
            
            await message.reply(info_text)
            
            # Forward the original file
            file_handler = FileHandler(config, database)
            
            forwarded = await file_handler.forward_file(
                client, file_info[1], file_info[6], message.chat.id
            )
            
            if forwarded:
                # Update download count
                await database.connection.execute("""
                    UPDATE files SET download_count = download_count + 1 WHERE file_id = ?
                """, (file_id,))
                await database.connection.commit()
                
                logger.info(f"File {file_id} downloaded by user {message.from_user.id}")
            else:
                await message.reply("❌ Error sending file. Please try again.")
                
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            await message.reply("❌ Error downloading file. Please try again.")
        
    except Exception as e:
        logger.error(f"Error in download command: {e}")
        await message.reply("❌ Error processing download command")

async def delete_file(client: Client, message: Message, database, config):
    """Handle file deletion (admin only)"""
    try:
        if not Utils.is_admin(message.from_user.id, config.ADMIN_IDS):
            await message.reply("❌ This command is for admins only.")
            return
        
        args = Utils.parse_command_args(message.text)
        
        if not args:
            await message.reply(
                "🗑️ **Delete File** (Admin Only)\n\n"
                "Usage: `/deletefile <file_id>`\n\n"
                "⚠️ **Warning:** This action cannot be undone!\n\n"
                "Example: `/deletefile ABC123`"
            )
            return
        
        file_id = args[0]
        
        # Get file info
        cursor = await database.connection.execute("""
            SELECT * FROM files WHERE file_id = ?
        """, (file_id,))
        
        file_info = await cursor.fetchone()
        
        if not file_info:
            await message.reply("❌ File not found.")
            return
        
        # Delete from database
        await database.connection.execute("""
            DELETE FROM files WHERE file_id = ?
        """, (file_id,))
        await database.connection.commit()
        
        await message.reply(
            f"✅ **File deleted successfully!**\n\n"
            f"📁 **File:** {file_info[2]}\n"
            f"👤 **Owner:** {file_info[1]}\n"
            f"🗑️ **Deleted by:** {message.from_user.first_name}"
        )
        
        # Notify file owner if different from admin
        if file_info[1] != message.from_user.id:
            try:
                await client.send_message(
                    file_info[1],
                    f"🗑️ **File Deleted**\n\n"
                    f"Your file **{file_info[2]}** has been deleted by an administrator.\n\n"
                    f"If you believe this was done in error, please contact support."
                )
            except:
                pass  # User might have blocked the bot
        
        logger.info(f"File {file_id} deleted by admin {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error in delete file command: {e}")
        await message.reply("❌ Error deleting file")

async def file_stats(client: Client, message: Message, database, config):
    """Handle file statistics (admin only)"""
    try:
        if not Utils.is_admin(message.from_user.id, config.ADMIN_IDS):
            await message.reply("❌ This command is for admins only.")
            return
        
        # Get file statistics
        cursor = await database.connection.execute("""
            SELECT 
                file_type,
                COUNT(*) as count,
                SUM(file_size) as total_size,
                AVG(file_size) as avg_size
            FROM files 
            GROUP BY file_type
            ORDER BY count DESC
        """)
        
        type_stats = await cursor.fetchall()
        
        # Get overall stats
        cursor = await database.connection.execute("""
            SELECT 
                COUNT(*) as total_files,
                SUM(file_size) as total_size,
                AVG(file_size) as avg_size,
                MAX(file_size) as max_size,
                MIN(file_size) as min_size
            FROM files
        """)
        
        overall_stats = await cursor.fetchone()
        
        stats_text = (
            f"📊 **File Statistics** (Admin)\n\n"
            f"📈 **Overall:**\n"
            f"• Total Files: {overall_stats[0]}\n"
            f"• Total Size: {Utils.format_file_size(overall_stats[1] or 0)}\n"
            f"• Average Size: {Utils.format_file_size(overall_stats[2] or 0)}\n"
            f"• Largest File: {Utils.format_file_size(overall_stats[3] or 0)}\n"
            f"• Smallest File: {Utils.format_file_size(overall_stats[4] or 0)}\n\n"
            
            f"📂 **By Type:**\n"
        )
        
        for file_type, count, total_size, avg_size in type_stats:
            stats_text += (
                f"**{file_type.title()}:** {count} files\n"
                f"  └ Total: {Utils.format_file_size(total_size)}\n"
                f"  └ Average: {Utils.format_file_size(avg_size)}\n"
            )
        
        await message.reply(stats_text)
        
    except Exception as e:
        logger.error(f"Error in file stats command: {e}")
        await message.reply("❌ Error getting file statistics")
