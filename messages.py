"""
Message handlers for the Telegram bot.
"""

import logging
import random
from telegram import Update
from telegram.ext import ContextTypes
from bot.utils import rate_limit, log_message, escape_markdown

logger = logging.getLogger(__name__)

# Predefined responses for different message types
GREETING_RESPONSES = [
    "Hello! 👋 How can I help you today?",
    "Hi there! 😊 What's on your mind?",
    "Greetings! 🤖 I'm here to assist you.",
    "Hey! 👋 Nice to meet you!"
]

POSITIVE_RESPONSES = [
    "That's great! 😊",
    "Awesome! 🎉",
    "Wonderful! ✨",
    "That sounds fantastic! 🌟"
]

QUESTION_RESPONSES = [
    "That's an interesting question! 🤔",
    "I'm still learning, but I'd love to help! 🤖",
    "Let me think about that... 💭",
    "Great question! 📝"
]

DEFAULT_RESPONSES = [
    "Thanks for your message! 💬",
    "I hear you! 👂",
    "Interesting! Tell me more. 🤔",
    "I'm processing what you said... 🤖",
    "Got it! Anything else I can help with? 😊"
]

@rate_limit(max_messages=15, window_seconds=60)
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle regular text messages from users.
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    log_message(update, "TEXT_MESSAGE")
    
    user = update.effective_user
    message_text = update.message.text.lower().strip()
    
    try:
        # Determine response based on message content
        response = generate_response(message_text, user.first_name)
        
        await update.message.reply_text(response)
        logger.info(f"Responded to user {user.id}")
        
    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        await update.message.reply_text(
            "Sorry, I encountered an error processing your message. Please try again! 🤖"
        )

def generate_response(message_text: str, user_name: str) -> str:
    """
    Generate an appropriate response based on the message content.
    
    Args:
        message_text: The user's message text (lowercase)
        user_name: The user's first name
        
    Returns:
        Generated response string
    """
    # Check for greetings
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
    if any(greeting in message_text for greeting in greetings):
        return f"{random.choice(GREETING_RESPONSES)}"
    
    # Check for positive words
    positive_words = ['good', 'great', 'awesome', 'amazing', 'wonderful', 'excellent', 'fantastic']
    if any(word in message_text for word in positive_words):
        return random.choice(POSITIVE_RESPONSES)
    
    # Check for questions
    question_indicators = ['?', 'what', 'how', 'when', 'where', 'why', 'who', 'which']
    if any(indicator in message_text for indicator in question_indicators):
        return random.choice(QUESTION_RESPONSES)
    
    # Check for thanks
    thanks_words = ['thank', 'thanks', 'thx']
    if any(word in message_text for word in thanks_words):
        return f"You're welcome, {user_name}! 😊 Happy to help!"
    
    # Check for bot-related words
    bot_words = ['bot', 'robot', 'ai', 'artificial', 'machine']
    if any(word in message_text for word in bot_words):
        return "Yes, I'm a bot! 🤖 I'm here to chat and help you out. What would you like to know?"
    
    # Check for help requests
    help_words = ['help', 'assist', 'support']
    if any(word in message_text for word in help_words):
        return "I'd be happy to help! 🆘 Try using /help to see what I can do, or just keep chatting with me!"
    
    # Default response
    return random.choice(DEFAULT_RESPONSES)

async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle errors that occur during bot operation.
    
    Args:
        update: Telegram update object (may be None)
        context: Telegram context object
    """
    logger.error(f"Update {update} caused error {context.error}")
    
    # Try to send error message to user if update is available
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "🚨 Oops! Something went wrong. Please try again later or contact support."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")
