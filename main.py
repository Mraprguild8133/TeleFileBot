#!/usr/bin/env python3
"""
Telegram Bot with URL Shortening and File Handling
Author: Mraprguild
"""

import asyncio
import logging
import os
from bot import Bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to start the bot"""
    try:
        # Initialize and start the bot
        bot = Bot()
        await bot.start()
        
        logger.info("Bot started successfully by Mraprguild")
        
        # Keep the bot running
        await bot.idle()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        logger.info("Bot stopped")

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("files", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    
    # Run the bot
    asyncio.run(main())
