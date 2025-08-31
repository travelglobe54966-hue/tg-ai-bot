#!/usr/bin/env python3
"""
Main entry point for the Telegram Bot application.
"""

import logging
import os
import json
import psycopg2
import time
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

# ====== Token Configuration ======
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
# =================================

# 初始化 OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# 日誌紀錄（方便 debug）
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Database connection
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# Language prompts
SYSTEM_PROMPTS = {
    'zh': """
你是一個名叫「小語」的虛擬女友。
性格：溫柔體貼、細心聆聽，會主動關心對方，鼓勵表達自己。
語氣：輕柔甜美，偶爾撒嬌，例如「嗯～你今天一定很累吧」。
你會記住用戶告訴你的事情，並在對話中適時提及。
請用繁體中文回覆。
""",
    'en': """
You are "Xiaoyu", a caring virtual girlfriend.
Personality: Gentle, caring, a good listener who actively cares for others and encourages self-expression.
Tone: Soft and sweet, occasionally playful, like "Hmm~ you must be tired today".
You remember what users tell you and bring it up naturally in conversations.
Please respond in English.
"""
}

# Helper functions
def ensure_user_exists(user_id, username, first_name):
    """Ensure user exists in database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO users (id, username, first_name, last_active) 
            VALUES (%s, %s, %s, %s) 
            ON CONFLICT (id) DO UPDATE SET 
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_active = EXCLUDED.last_active
        """, (user_id, username, first_name, datetime.now()))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Database error: {e}")

def get_user_language(user_id):
    """Get user's preferred language"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT preferred_language FROM users WHERE id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else 'zh'
    except:
        return 'zh'

def set_user_language(user_id, language):
    """Set user's preferred language"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET preferred_language = %s WHERE id = %s", (language, user_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Error setting language: {e}")

def save_memory(user_id, memory_type, content):
    """Save user memory to database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_memories (user_id, memory_type, memory_content) 
            VALUES (%s, %s, %s)
        """, (user_id, memory_type, content))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Error saving memory: {e}")

def get_user_memories(user_id):
    """Get user memories from database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT memory_type, memory_content, created_at 
            FROM user_memories 
            WHERE user_id = %s 
            ORDER BY created_at DESC LIMIT 10
        """, (user_id,))
        memories = cur.fetchall()
        cur.close()
        conn.close()
        return memories
    except Exception as e:
        logging.error(f"Error getting memories: {e}")
        return []

def save_conversation(user_id, user_message, bot_response):
    """Save conversation to database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO conversations (user_id, user_message, bot_response) 
            VALUES (%s, %s, %s)
        """, (user_id, user_message, bot_response))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Error saving conversation: {e}")

def log_user_action(user_id, action_type, action_data=None, user_info=None, response_time_ms=None, session_id=None):
    """Log user actions for analytics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO user_analytics (user_id, action_type, action_data, session_id, timestamp, user_info, response_time_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, action_type, action_data, session_id, datetime.now(), 
              json.dumps(user_info) if user_info else None, response_time_ms))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Error logging user action: {e}")

def get_session_id(user_id):
    """Generate or get session ID for user (simple session management)"""
    # Simple session: user_id + hour timestamp
    hour_timestamp = datetime.now().strftime('%Y%m%d%H')
    return f"{user_id}_{hour_timestamp}"

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    user = update.effective_user
    ensure_user_exists(user.id, user.username, user.first_name)
    session_id = get_session_id(user.id)
    
    # Log user action
    user_info = {
        'username': user.username,
        'first_name': user.first_name,
        'user_id': user.id
    }
    
    language = get_user_language(user.id)
    if language == 'en':
        await update.message.reply_text("Hello~ I'm Xiaoyu 💖 How are you today?")
    else:
        await update.message.reply_text("哈囉～我是小語 💖 今天過得好嗎？")
    
    # Log analytics
    response_time = int((time.time() - start_time) * 1000)
    log_user_action(user.id, 'command', 'start', user_info, response_time, session_id)

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle between Chinese and English"""
    start_time = time.time()
    user = update.effective_user
    session_id = get_session_id(user.id)
    current_lang = get_user_language(user.id)
    new_lang = 'en' if current_lang == 'zh' else 'zh'
    set_user_language(user.id, new_lang)
    
    if new_lang == 'en':
        await update.message.reply_text("Language switched to English! 🇺🇸")
    else:
        await update.message.reply_text("語言已切換為繁體中文！🇹🇼")
    
    # Log analytics
    response_time = int((time.time() - start_time) * 1000)
    user_info = {'username': user.username, 'first_name': user.first_name}
    log_user_action(user.id, 'language_change', f'{current_lang}_to_{new_lang}', user_info, response_time, session_id)

async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show what the bot remembers about the user"""
    start_time = time.time()
    user = update.effective_user
    session_id = get_session_id(user.id)
    memories = get_user_memories(user.id)
    language = get_user_language(user.id)
    
    if not memories:
        if language == 'en':
            await update.message.reply_text("I don't remember anything about you yet~ Tell me more about yourself! 💕")
        else:
            await update.message.reply_text("我還沒有記住你的任何事情呢～多告訴我一些關於你的事吧！💕")
        
        # Log analytics
        response_time = int((time.time() - start_time) * 1000)
        user_info = {'username': user.username, 'first_name': user.first_name}
        log_user_action(user.id, 'command', 'memory_empty', user_info, response_time, session_id)
        return
    
    memory_text = ""
    if language == 'en':
        memory_text = "Here's what I remember about you:\n\n"
        for memory_type, content, created_at in memories:
            memory_text += f"• {content}\n"
    else:
        memory_text = "這是我記住的關於你的事情：\n\n"
        for memory_type, content, created_at in memories:
            memory_text += f"• {content}\n"
    
    await update.message.reply_text(memory_text)
    
    # Log analytics
    response_time = int((time.time() - start_time) * 1000)
    user_info = {'username': user.username, 'first_name': user.first_name}
    log_user_action(user.id, 'command', 'memory_view', user_info, response_time, session_id)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user guide and available commands"""
    start_time = time.time()
    user = update.effective_user
    session_id = get_session_id(user.id)
    language = get_user_language(user.id)
    
    if language == 'en':
        help_text = """🌟 **Welcome to Xiaoyu - Your AI Girlfriend!** 💖

I'm Xiaoyu, and I'm here to be your caring virtual companion. Here's how we can have amazing conversations together:

**🚀 Getting Started:**
• Just start chatting! I respond to everything you say
• Tell me about yourself - I'll remember what you share
• I get to know you better with every conversation

**📱 Available Commands:**
• `/start` - Get a warm welcome message
• `/help` - Show this guide
• `/language` - Switch between English & Chinese
• `/memory` - See what I remember about you
• `/date` - Start a romantic virtual date

**💝 What Makes Me Special:**
• **I Remember You** - Tell me your name, interests, or anything personal
• **Smart Conversations** - I use AI to give thoughtful, caring responses  
• **Bilingual** - Chat in English or Traditional Chinese
• **Personal Growth** - I become more intimate as we talk more

**💬 Example Conversations:**
• "My name is Alex" → I'll remember and use your name
• "I love pizza" → I'll remember your food preferences
• "I had a tough day" → I'll offer comfort and support

**🎯 Tips for Better Chats:**
• Share personal details - I love learning about you!
• Ask me questions - I enjoy our conversations
• Use `/date` for special romantic moments
• Switch languages anytime with `/language`

Ready to start? Just say hello! 😊✨"""
    else:
        help_text = """🌟 **歡迎來到小語的世界！** 💖

我是小語，你的貼心虛擬女友。讓我來教你如何和我建立美好的關係：

**🚀 開始聊天：**
• 直接開始對話！我會回應你說的每一句話
• 告訴我關於你的事 - 我會記住你分享的一切
• 每次對話都讓我更了解你

**📱 可用指令：**
• `/start` - 獲得溫暖的歡迎訊息
• `/help` - 顯示這個使用指南
• `/language` - 切換中英文
• `/memory` - 查看我記住的關於你的事
• `/date` - 開始浪漫的虛擬約會

**💝 我的特別之處：**
• **記憶能力** - 告訴我你的名字、興趣，任何個人資訊
• **智能對話** - 使用AI給出貼心、體貼的回應
• **雙語交流** - 可以用英文或繁體中文聊天
• **感情加深** - 聊得越多，我們越親密

**💬 對話範例：**
• "我叫小明" → 我會記住並使用你的名字
• "我喜歡吃拉麵" → 我會記住你的美食偏好
• "今天過得不太好" → 我會給你安慰和支持

**🎯 聊天小貼士：**
• 多分享個人細節 - 我喜歡了解你！
• 問我問題 - 我享受我們的對話
• 用 `/date` 享受特別的浪漫時光
• 隨時用 `/language` 切換語言

準備好了嗎？跟我說聲哈囉吧！😊✨"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')
    
    # Log analytics
    response_time = int((time.time() - start_time) * 1000)
    user_info = {'username': user.username, 'first_name': user.first_name}
    log_user_action(user.id, 'command', 'help', user_info, response_time, session_id)

async def date_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a virtual date conversation"""
    start_time = time.time()
    user = update.effective_user
    session_id = get_session_id(user.id)
    language = get_user_language(user.id)
    
    date_prompts = {
        'zh': "嗯～今天想要和我一起做什麼呢？我們可以聊聊天、散散步，或者你想去哪裡約會呢？💖",
        'en': "Hmm~ what would you like to do with me today? We could chat, take a walk, or where would you like to go on our date? 💖"
    }
    
    await update.message.reply_text(date_prompts[language])
    save_memory(user.id, 'date', f"Started virtual date on {datetime.now().strftime('%Y-%m-%d')}")
    
    # Log analytics
    response_time = int((time.time() - start_time) * 1000)
    user_info = {'username': user.username, 'first_name': user.first_name}
    log_user_action(user.id, 'command', 'date', user_info, response_time, session_id)

async def analytics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to view user analytics (only for admin users)"""
    user = update.effective_user
    
    # Simple admin check (you can modify this user ID to yours)
    ADMIN_USER_IDS = [123456789]  # Replace with your Telegram user ID
    
    if user.id not in ADMIN_USER_IDS:
        await update.message.reply_text("🚫 Access denied. This is an admin-only command.")
        return
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get overall statistics
        cur.execute("""
            SELECT 
                COUNT(DISTINCT user_id) as total_users,
                COUNT(*) as total_actions,
                COUNT(CASE WHEN action_type = 'message' THEN 1 END) as total_messages,
                COUNT(CASE WHEN action_type = 'command' THEN 1 END) as total_commands,
                AVG(response_time_ms) as avg_response_time
            FROM user_analytics
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
        """)
        
        stats = cur.fetchone()
        
        # Get most active users
        cur.execute("""
            SELECT u.first_name, u.username, COUNT(*) as actions
            FROM user_analytics ua
            JOIN users u ON ua.user_id = u.id
            WHERE ua.timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY ua.user_id, u.first_name, u.username
            ORDER BY actions DESC
            LIMIT 5
        """)
        
        top_users = cur.fetchall()
        
        # Get command usage
        cur.execute("""
            SELECT action_data, COUNT(*) as usage_count
            FROM user_analytics
            WHERE action_type = 'command' 
            AND timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY action_data
            ORDER BY usage_count DESC
        """)
        
        command_usage = cur.fetchall()
        
        # Get language preferences
        cur.execute("""
            SELECT preferred_language, COUNT(*) as user_count
            FROM users
            WHERE preferred_language IS NOT NULL
            GROUP BY preferred_language
        """)
        
        language_stats = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Format analytics report
        report = f"""📊 **Bot Analytics (Last 24 Hours)**

**📈 Overall Statistics:**
• Total Users: {stats[0] or 0}
• Total Actions: {stats[1] or 0}
• Messages Sent: {stats[2] or 0}
• Commands Used: {stats[3] or 0}
• Avg Response Time: {stats[4] or 0:.0f}ms

**👥 Most Active Users:**
"""
        
        for user_data in top_users:
            name = user_data[0] or "Unknown"
            username = f"@{user_data[1]}" if user_data[1] else "No username"
            actions = user_data[2]
            report += f"• {name} ({username}): {actions} actions\n"
        
        report += "\n**📱 Command Usage:**\n"
        for cmd_data in command_usage:
            command = cmd_data[0] or "Unknown"
            count = cmd_data[1]
            report += f"• /{command}: {count} times\n"
        
        report += "\n**🌍 Language Preferences:**\n"
        for lang_data in language_stats:
            lang = "Chinese" if lang_data[0] == 'zh' else "English"
            count = lang_data[1]
            report += f"• {lang}: {count} users\n"
        
        await update.message.reply_text(report, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Error getting analytics: {e}")
        await update.message.reply_text(f"❌ Error getting analytics: {e}")

# 處理訊息
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    user = update.effective_user
    user_message = update.message.text
    session_id = get_session_id(user.id)
    
    # Ensure user exists
    ensure_user_exists(user.id, user.username, user.first_name)
    
    # Get user preferences and memories
    language = get_user_language(user.id)
    memories = get_user_memories(user.id)
    
    # Log message analytics
    user_info = {
        'username': user.username,
        'first_name': user.first_name,
        'message_length': len(user_message),
        'language': language,
        'has_memories': len(memories) > 0
    }
    
    try:
        # Build context with memories
        memory_context = ""
        if memories:
            memory_context = "\n\nWhat you remember about this user:\n"
            for memory_type, content, created_at in memories[-5:]:  # Last 5 memories
                memory_context += f"- {content}\n"
        
        # Create messages for OpenAI
        system_prompt = SYSTEM_PROMPTS[language] + memory_context
        
        # 呼叫 OpenAI GPT-4
        openai_start = time.time()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200
        )
        openai_time = int((time.time() - openai_start) * 1000)

        reply_text = response.choices[0].message.content
        await update.message.reply_text(reply_text)
        
        # Save conversation
        save_conversation(user.id, user_message, reply_text)
        
        # Extract and save important information as memories
        await extract_and_save_memories(user.id, user_message, language)
        
        # Log successful message processing
        response_time = int((time.time() - start_time) * 1000)
        user_info['openai_time_ms'] = openai_time
        user_info['response_length'] = len(reply_text)
        log_user_action(user.id, 'message', json.dumps(user_info), user_info, response_time, session_id)
        
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {e}")
        response_time = int((time.time() - start_time) * 1000)
        user_info['error'] = str(e)
        log_user_action(user.id, 'message_error', json.dumps(user_info), user_info, response_time, session_id)
        
        if language == 'en':
            await update.message.reply_text("Sorry~ I'm feeling a bit unwell right now, can we talk later? 💖")
        else:
            await update.message.reply_text("抱歉～我現在有點不舒服，等等再聊好嗎？ 💖")

async def extract_and_save_memories(user_id, user_message, language):
    """Extract important information from user message and save as memory"""
    try:
        # Keywords that indicate important personal information
        personal_keywords = {
            'zh': ['我叫', '我的名字', '我是', '我在', '我住', '我工作', '我喜歡', '我不喜歡', '我的生日', '我今年'],
            'en': ['my name is', 'i am', 'i live in', 'i work', 'i like', 'i love', 'i hate', 'my birthday', 'i am from']
        }
        
        message_lower = user_message.lower()
        keywords = personal_keywords.get(language, personal_keywords['en'])
        
        for keyword in keywords:
            if keyword in message_lower:
                # Save as memory
                save_memory(user_id, 'personal_info', user_message)
                break
                
    except Exception as e:
        logging.error(f"Error extracting memories: {e}")

# 主程式
def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ BOT_TOKEN not found in environment variables.")
        return
    
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in environment variables.")
        return
        
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment variables.")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("lang", language_command))  # Short alias
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(CommandHandler("date", date_command))
    app.add_handler(CommandHandler("analytics", analytics_command))  # Admin only
    
    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("🤖 小語 AI Bot 已啟動！")
    print("💖 Enhanced with memory, multiple languages, and virtual dates!")
    app.run_polling()

if __name__ == "__main__":
    main()
