import re

class MessageFilter:
    def __init__(self, db):
        self.db = db
    
    def check_message(self, message, chat_id):
        settings = self.db.get_group_settings(chat_id)
        
        if settings['link_filter']:
            # Check for links and usernames
            if re.search(r'(https?://\S+)|(@\w+)', message.text or ''):
                return False
                
        if settings['banned_words']:
            # Check for banned words
            text = (message.text or '').lower()
            for word in settings['banned_words']:
                if word.lower() in text:
                    return False
                    
        return True 