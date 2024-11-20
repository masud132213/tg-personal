from pymongo import MongoClient
import os

class Database:
    def __init__(self):
        self.client = MongoClient(os.environ.get('MONGODB_URI'))
        self.db = self.client['cinemazbdbot']
        
    def get_group_settings(self, chat_id):
        return self.db.group_settings.find_one({'chat_id': chat_id}) or {
            'chat_id': chat_id,
            'link_filter': False,
            'welcome_msg': False,
            'clean_service': False,
            'website_link': '',
            'banned_words': [],
            'banned_users': [],
            'muted_users': [],
            'warn_counts': {}
        }
    
    def update_group_settings(self, chat_id, settings):
        self.db.group_settings.update_one(
            {'chat_id': chat_id},
            {'$set': settings},
            upsert=True
        )
    
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