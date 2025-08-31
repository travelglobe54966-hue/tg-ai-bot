"""
Utility functions for the Telegram bot.
"""

import logging
import time
from typing import Dict, List
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

# Simple in-memory rate limiting storage
user_message_times: Dict[int, List[float]] = {}

def setup_logging():
    """Setup logging configuration for the bot."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )
    
    # Set telegram library logging to WARNING to reduce noise
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)

def rate_limit(max_messages: int = 10, window_seconds: int = 60):
    """
    Rate limiting decorator for message handlers.
    
    Args:
        max_messages: Maximum number of messages allowed in the time window
        window_seconds: Time window in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            current_time = time.time()
            
            # Initialize user message times if not exists
            if user_id not in user_message_times:
                user_message_times[user_id] = []
            
            # Clean old messages outside the time window
            user_message_times[user_id] = [
                msg_time for msg_time in user_message_times[user_id]
                if current_time - msg_time < window_seconds
            ]
            
            # Check if user exceeded rate limit
            if len(user_message_times[user_id]) >= max_messages:
                await update.message.reply_text(
                    f"⚠️ Rate limit exceeded. Please wait {window_seconds} seconds before sending more messages."
                )
                return
            
            # Add current message time
            user_message_times[user_id].append(current_time)
            
            # Call the original function
            return await func(update, context)
        
        return wrapper
    return decorator

def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for MarkdownV2
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

def get_user_info(update: Update) -> str:
    """
    Get formatted user information from update.
    
    Args:
        update: Telegram update object
        
    Returns:
        Formatted user information string
    """
    user = update.effective_user
    chat = update.effective_chat
    
    info = f"User: {user.first_name}"
    if user.last_name:
        info += f" {user.last_name}"
    if user.username:
        info += f" (@{user.username})"
    info += f" (ID: {user.id})"
    
    if chat.type != "private":
        info += f"\nChat: {chat.title} (ID: {chat.id})"
    
    return info

def log_message(update: Update, action: str):
    """
    Log user message for monitoring.
    
    Args:
        update: Telegram update object
        action: Action description
    """
    logger = logging.getLogger(__name__)
    user_info = get_user_info(update)
    message_text = update.message.text if update.message and update.message.text else "N/A"
    
    logger.info(f"{action} - {user_info} - Message: {message_text}")
