from pymongo import MongoClient
import os

class Database:
    def __init__(self):
        try:
            self.client = MongoClient(os.environ.get('MONGODB_URI'))
            self.db = self.client['cinemazbdbot']
            print("MongoDB connected successfully!")
        except Exception as e:
            print(f"MongoDB connection error: {e}")
        
    def get_group_settings(self, chat_id):
        try:
            settings = self.db.group_settings.find_one({'chat_id': chat_id})
            if not settings:
                # Initialize default settings
                default_settings = {
                    'chat_id': chat_id,
                    'link_filter': False,
                    'welcome_msg': True,  # Default welcome message ON
                    'clean_service': True,  # Default service message cleaning ON
                    'website_link': 'https://t.me/cinemazbd_pm',
                    'banned_words': [],
                    'banned_users': [],
                    'muted_users': [],
                    'warn_counts': {}
                }
                self.db.group_settings.insert_one(default_settings)
                return default_settings
            return settings
        except Exception as e:
            print(f"Error getting group settings: {e}")
            return {
                'chat_id': chat_id,
                'link_filter': False,
                'welcome_msg': True,
                'clean_service': True,
                'website_link': 'https://t.me/cinemazbd_pm',
                'banned_words': [],
                'banned_users': [],
                'muted_users': [],
                'warn_counts': {}
            }
    
    def update_group_settings(self, chat_id, settings):
        try:
            self.db.group_settings.update_one(
                {'chat_id': chat_id},
                {'$set': settings},
                upsert=True
            )
            print(f"Settings updated for chat {chat_id}")
        except Exception as e:
            print(f"Error updating settings: {e}")
    
    def add_banned_user(self, chat_id, user_id):
        self.db.group_settings.update_one(
            {'chat_id': chat_id},
            {'$addToSet': {'banned_users': user_id}}
        )
    
    def add_muted_user(self, chat_id, user_id):
        self.db.group_settings.update_one(
            {'chat_id': chat_id},
            {'$addToSet': {'muted_users': user_id}}
        )
    
    def increment_warn(self, chat_id, user_id):
        result = self.db.group_settings.update_one(
            {'chat_id': chat_id},
            {'$inc': {f'warn_counts.{user_id}': 1}}
        )
        settings = self.get_group_settings(chat_id)
        return settings.get('warn_counts', {}).get(str(user_id), 0) 