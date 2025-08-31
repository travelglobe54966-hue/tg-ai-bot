"""
Command handlers for the Telegram bot.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.utils import rate_limit, log_message, escape_markdown

logger = logging.getLogger(__name__)

@rate_limit(max_messages=5, window_seconds=60)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command.
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    log_message(update, "START_COMMAND")
    
    user = update.effective_user
    welcome_message = f"""
🤖 *Welcome to the Telegram Bot, {escape_markdown(user.first_name)}!*

I'm here to help you with various tasks. Here's what I can do:

• Respond to your messages
• Handle various commands
• Provide helpful information

Use /help to see all available commands.

Let's get started! 🚀
"""
    
    try:
        await update.message.reply_text(
            welcome_message,
            parse_mode='MarkdownV2'
        )
        logger.info(f"Sent welcome message to user {user.id}")
    except Exception as e:
        logger.error(f"Error sending start message: {e}")
        await update.message.reply_text(
            "Welcome! I'm your Telegram bot. Use /help to see what I can do."
        )

@rate_limit(max_messages=5, window_seconds=60)
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /help command.
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    log_message(update, "HELP_COMMAND")
    
    help_message = """
📋 *Available Commands:*

/start \\- Start the bot and see welcome message
/help \\- Show this help message
/echo \\<text\\> \\- Echo back your message

💬 *Message Handling:*
Just send me any text message and I'll respond\\!

🛡️ *Rate Limiting:*
To prevent spam, there are limits on how many messages you can send per minute\\.

❓ *Need Help?*
If you encounter any issues, please contact the bot administrator\\.
"""
    
    try:
        await update.message.reply_text(
            help_message,
            parse_mode='MarkdownV2'
        )
        logger.info(f"Sent help message to user {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error sending help message: {e}")
        await update.message.reply_text(
            "Available commands:\n"
            "/start - Start the bot\n"
            "/help - Show help\n"
            "/echo <text> - Echo your message\n\n"
            "Just send me any message and I'll respond!"
        )

@rate_limit(max_messages=10, window_seconds=60)
async def echo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /echo command.
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    log_message(update, "ECHO_COMMAND")
    
    # Get the text after the command
    text_to_echo = " ".join(context.args) if context.args else ""
    
    if not text_to_echo:
        await update.message.reply_text(
            "📢 Please provide text to echo!\n\n"
            "Usage: /echo <your message here>"
        )
        return
    
    try:
        # Echo the message back with some formatting
        echo_message = f"🔄 *Echo:*\n{escape_markdown(text_to_echo)}"
        await update.message.reply_text(
            echo_message,
            parse_mode='MarkdownV2'
        )
        logger.info(f"Echoed message for user {update.effective_user.id}: {text_to_echo}")
    except Exception as e:
        logger.error(f"Error in echo command: {e}")
        await update.message.reply_text(f"Echo: {text_to_echo}")
