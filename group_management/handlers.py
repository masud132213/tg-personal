from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
from .database import Database
from .welcome import WelcomeManager
from .filters import MessageFilter
import time

class GroupManagement:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.welcome = WelcomeManager()
        self.filter = MessageFilter(self.db)
        
        # We'll add handlers later in setup_handlers method
        
    def setup_handlers(self, dispatcher):
        """Setup all handlers after dispatcher is ready"""
        dispatcher.add_handler(CommandHandler('group', self.group_settings))
        dispatcher.add_handler(CommandHandler('ban', self.ban_user))
        dispatcher.add_handler(CommandHandler('mute', self.mute_user))
        dispatcher.add_handler(CallbackQueryHandler(self.button_callback, pattern='^group_'))

    def is_admin(self, update):
        """Check if user is admin in the group"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Check if user is in OWNER_IDS
        if user_id in [7202314047, 1826754085]:
            return True
            
        try:
            chat_member = update.effective_chat.get_member(user_id)
            return chat_member.status in ['creator', 'administrator']
        except Exception:
            return False
            
    def group_settings(self, update, context):
        if not self.is_admin(update):
            update.message.reply_text("এই কমান্ড শুধু অ্যাডমিনদের জন্য!")
            return
            
        chat_id = update.effective_chat.id
        settings = self.db.get_group_settings(chat_id)
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"লিংক ফিল্টার: {'✅' if settings['link_filter'] else '❌'}", 
                    callback_data=f"group_link_{chat_id}"
                )
            ],
            [
                InlineKeyboardButton("ব্যান ওয়ার্ড", callback_data=f"group_banword_{chat_id}"),
                InlineKeyboardButton("ব্যান ইউজার", callback_data=f"group_banuser_{chat_id}")
            ],
            [
                InlineKeyboardButton("মিউট ইউজার", callback_data=f"group_mute_{chat_id}"),
                InlineKeyboardButton(
                    f"ওয়েলকাম: {'✅' if settings['welcome_msg'] else '❌'}", 
                    callback_data=f"group_welcome_{chat_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    f"সার্ভিস মেসেজ: {'✅' if settings['clean_service'] else '❌'}", 
                    callback_data=f"group_service_{chat_id}"
                )
            ],
            [
                InlineKeyboardButton("ওয়েবসাইট লিংক সেট", callback_data=f"group_website_{chat_id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("গ্রুপ সেটিংস:", reply_markup=reply_markup)

    def ban_user(self, update, context):
        if not self.is_admin(update):
            update.message.reply_text("এই কমান্ড শুধু অ্যাডমিনদের জন্য!")
            return
            
        # Check if command is a reply to a message
        if not update.message.reply_to_message:
            update.message.reply_text("একজন ইউজারকে ব্যান করতে তার মেসেজে রিপ্লাই দিয়ে কমান্ড দিন।")
            return
            
        chat_id = update.effective_chat.id
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.first_name
        
        try:
            # Ban the user
            context.bot.ban_chat_member(chat_id, user_id)
            
            # Add to database
            self.db.add_banned_user(chat_id, user_id)
            
            update.message.reply_text(f"ইউজার {user_name} কে ব্যান করা হয়েছে।")
            
        except Exception as e:
            update.message.reply_text(f"ব্যান করতে সমস্যা হয়েছে: {str(e)}")

    def mute_user(self, update, context):
        if not self.is_admin(update):
            update.message.reply_text("এই কমান্ড শুধু অ্যাডমিনদের জন্য!")
            return
            
        if not update.message.reply_to_message:
            update.message.reply_text("একজন ইউজারকে মিউট করতে তার মেসেজে রিপ্লাই দিয়ে কমান্ড দিন।")
            return
            
        chat_id = update.effective_chat.id
        user_id = update.message.reply_to_message.from_user.id
        user_name = update.message.reply_to_message.from_user.first_name
        
        try:
            # Get current warn count
            warn_count = self.db.increment_warn(chat_id, user_id)
            
            if warn_count >= 5:
                # Ban user after 5 warnings
                context.bot.ban_chat_member(chat_id, user_id)
                self.db.add_banned_user(chat_id, user_id)
                update.message.reply_text(
                    f"ইউজার {user_name} কে 5টি ওয়ার্নিং এর কারণে ব্যান করা হয়েছে।"
                )
            else:
                # Mute for 24 hours
                until_date = int(time.time() + 24 * 60 * 60)
                context.bot.restrict_chat_member(
                    chat_id, 
                    user_id,
                    until_date=until_date,
                    permissions={
                        'can_send_messages': False,
                        'can_send_media_messages': False,
                        'can_send_other_messages': False,
                        'can_add_web_page_previews': False
                    }
                )
                
                # Add to database
                self.db.add_muted_user(chat_id, user_id)
                
                update.message.reply_text(
                    f"ইউজার {user_name} কে 24 ঘণ্টার জন্য মিউট করা হয়েছে।\n"
                    f"বর্তমান ওয়ার্নিং: {warn_count}/5"
                )
                
        except Exception as e:
            update.message.reply_text(f"মিউট করতে সমস্যা হয়েছে: {str(e)}")

    def button_callback(self, update, context):
        query = update.callback_query
        data = query.data
        
        if data.startswith('group_'):
            parts = data.split('_')
            action = parts[1]
            chat_id = int(parts[2])
            
            settings = self.db.get_group_settings(chat_id)
            
            if action == 'link':
                settings['link_filter'] = not settings['link_filter']
            elif action == 'welcome':
                settings['welcome_msg'] = not settings['welcome_msg']
            elif action == 'service':
                settings['clean_service'] = not settings['clean_service']
                
            self.db.update_group_settings(chat_id, settings)
            
            # Update the keyboard
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"লিংক ফিল্টার: {'✅' if settings['link_filter'] else '❌'}", 
                        callback_data=f"group_link_{chat_id}"
                    )
                ],
                [
                    InlineKeyboardButton("ব্যান ওয়ার্ড", callback_data=f"group_banword_{chat_id}"),
                    InlineKeyboardButton("ব্যান ইউজার", callback_data=f"group_banuser_{chat_id}")
                ],
                [
                    InlineKeyboardButton("মিউট ইউজার", callback_data=f"group_mute_{chat_id}"),
                    InlineKeyboardButton(
                        f"ওয়েলকাম: {'✅' if settings['welcome_msg'] else '❌'}", 
                        callback_data=f"group_welcome_{chat_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"সার্ভিস মেসেজ: {'✅' if settings['clean_service'] else '❌'}", 
                        callback_data=f"group_service_{chat_id}"
                    )
                ],
                [
                    InlineKeyboardButton("ওয়েবসাইট লিংক সেট", callback_data=f"group_website_{chat_id}")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.message.edit_reply_markup(reply_markup=reply_markup)
            query.answer("সেটিংস আপডেট করা হয়েছে!")

    # Continue in next message due to length... 