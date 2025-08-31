"""
Configuration management for the Telegram bot.
"""

import os
from typing import Optional

class Config:
    """Configuration class for bot settings."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.bot_token: Optional[str] = os.getenv("BOT_TOKEN")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.webhook_url: Optional[str] = os.getenv("WEBHOOK_URL")
        self.port: int = int(os.getenv("PORT", "8000"))
        
        # Rate limiting settings
        self.rate_limit_messages: int = int(os.getenv("RATE_LIMIT_MESSAGES", "10"))
        self.rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        
        # Bot settings
        self.bot_name: str = os.getenv("BOT_NAME", "MyTelegramBot")
        self.admin_user_ids: list = self._parse_admin_ids()
    
    def _parse_admin_ids(self) -> list:
        """Parse admin user IDs from environment variable."""
        admin_ids_str = os.getenv("ADMIN_USER_IDS", "")
        if not admin_ids_str:
            return []
        
        try:
            return [int(user_id.strip()) for user_id in admin_ids_str.split(",") if user_id.strip()]
        except ValueError:
            return []
    
    def is_admin(self, user_id: int) -> bool:
        """Check if a user is an admin."""
        return user_id in self.admin_user_ids
