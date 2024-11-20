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
        
        # Add handlers
        bot.dispatcher.add_handler(CommandHandler('group', self.group_settings))
        bot.dispatcher.add_handler(CommandHandler('ban', self.ban_user))
        bot.dispatcher.add_handler(CommandHandler('mute', self.mute_user))
        bot.dispatcher.add_handler(CallbackQueryHandler(self.button_callback, pattern='^group_'))
        
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

    # Continue in next message due to length... 