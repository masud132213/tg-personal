from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from .database import Database
from .welcome import WelcomeManager
from .filters import MessageFilter
import time, re
import os

# Get owner IDs from environment
OWNER_IDS = [7202314047, 1826754085]

class GroupManagement:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.welcome = WelcomeManager()
        self.filter = MessageFilter(self.db)
        
    def is_admin(self, update):
        """Check if user is admin or owner"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Check if user is in OWNER_IDS
        if user_id in OWNER_IDS:
            return True
            
        # Check if user is admin in the group
        try:
            chat_member = update.effective_chat.get_member(user_id)
            return chat_member.status in ['creator', 'administrator']
        except Exception:
            return False

    def setup_handlers(self, dispatcher):
        """Setup all handlers after dispatcher is ready"""
        dispatcher.add_handler(CommandHandler('group', self.group_settings))
        dispatcher.add_handler(CommandHandler('ban', self.ban_user))
        dispatcher.add_handler(CommandHandler('mute', self.mute_user))
        dispatcher.add_handler(CommandHandler('setwebsite', self.set_website))
        dispatcher.add_handler(CallbackQueryHandler(self.button_callback, pattern='^group_'))
        dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, self.welcome_new_member))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))

    def group_settings(self, update, context):
        """Handle /group command"""
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
                InlineKeyboardButton(
                    f"ওয়েবসাইট লিংক: {'✅' if settings.get('website_link') else '❌'}", 
                    callback_data=f"group_website_{chat_id}"
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("গ্রুপ সেটিংস:", reply_markup=reply_markup)

    def set_website(self, update, context):
        """Set website link for the group"""
        if not self.is_admin(update):
            update.message.reply_text("এই কমান্ড শুধু অ্যাডমিনদের জন্য!")
            return
            
        if not context.args:
            update.message.reply_text("ওয়েবসাইট লিংক দিন। উদাহরণ: /setwebsite https://example.com")
            return
            
        chat_id = update.effective_chat.id
        website_link = context.args[0]
        
        settings = self.db.get_group_settings(chat_id)
        settings['website_link'] = website_link
        self.db.update_group_settings(chat_id, settings)
        
        update.message.reply_text("ওয়েবসাইট লিংক সেট করা হয়েছে!")

    def welcome_new_member(self, update, context):
        """Welcome new members"""
        try:
            chat_id = update.effective_chat.id
            settings = self.db.get_group_settings(chat_id)
            
            if not settings.get('welcome_msg', False):
                return
                
            for new_member in update.message.new_chat_members:
                if new_member.is_bot:
                    continue
                    
                website_link = settings.get('website_link', '')
                message, buttons = self.welcome.get_random_template(new_member.first_name, website_link)
                
                # Create InlineKeyboardMarkup from buttons
                if buttons:
                    keyboard = []
                    for button in buttons:
                        keyboard.append([
                            InlineKeyboardButton(
                                text=button['text'],
                                url=button['url']
                            )
                        ])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                else:
                    reply_markup = None
                
                # Send welcome message
                welcome_msg = context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                
                # Delete service message if enabled
                if settings.get('clean_service', False):
                    try:
                        # Delete the "X joined the group" message
                        update.message.delete()
                    except Exception as e:
                        print(f"Error deleting service message: {e}")
                
                # Delete welcome message after 3 seconds
                if welcome_msg:
                    context.job_queue.run_once(
                        lambda ctx: self.delete_message_safe(chat_id, welcome_msg.message_id, context.bot),
                        3
                    )
                    
        except Exception as e:
            print(f"Error in welcome_new_member: {e}")

    def delete_message_safe(self, chat_id, message_id, bot):
        """Safely delete a message"""
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"Error deleting message: {e}")

    def handle_message(self, update, context):
        """Handle regular messages"""
        if not update.message or not update.message.text:
            return
            
        chat_id = update.effective_chat.id
        settings = self.db.get_group_settings(chat_id)
        
        # Check link filter
        if settings.get('link_filter', False):
            text = update.message.text
            
            # Check for links and usernames
            if any(x in text.lower() for x in ['http://', 'https://', '.com', '.org', '.net']) or \
               re.search(r'@[\w]+', text) or \
               re.search(r't\.me/[\w]+', text):
                try:
                    # Delete message
                    update.message.delete()
                    
                    # Send warning
                    warning = (
                        f"⚠️ {update.message.from_user.first_name},\n"
                        "গ্রুপে লিংক/ইউজারনেম শেয়ার করা নিষিদ্ধ!"
                    )
                    msg = update.message.reply_text(warning)
                    
                    # Delete warning after 3 seconds
                    context.job_queue.run_once(
                        lambda _: self.delete_message_safe(chat_id, msg.message_id),
                        3
                    )
                    return
                except Exception:
                    pass

    def ban_user(self, update, context):
        if not self.is_admin(update):
            update.message.reply_text("এই কমান্ড শুধু অ্যাডমিনদের জন্য!")
            return
            
        chat_id = update.effective_chat.id
        user_to_ban = None
        
        # Check if command is a reply
        if update.message.reply_to_message:
            user_to_ban = update.message.reply_to_message.from_user
        # Check if username is provided
        elif context.args:
            username = context.args[0].replace("@", "")
            try:
                chat_member = context.bot.get_chat_member(chat_id, username)
                user_to_ban = chat_member.user
            except Exception:
                update.message.reply_text("ইউজার পাওয়া যায়নি!")
                return
        else:
            update.message.reply_text("একজন ইউজারকে ব্যান করতে তার মেসেজে রিপ্লাই দিন অথবা ইউজারনেম দিন।")
            return
            
        try:
            # Ban the user
            context.bot.ban_chat_member(chat_id, user_to_ban.id)
            
            # Add to database
            self.db.add_banned_user(chat_id, user_to_ban.id)
            
            update.message.reply_text(f"ইউজার {user_to_ban.first_name} কে ব্যান করা হয়েছে।")
            
        except Exception as e:
            update.message.reply_text(f"ব্যান করতে সমস্যা হয়েছে: {str(e)}")

    def mute_user(self, update, context):
        if not self.is_admin(update):
            update.message.reply_text("এই কমান্ড শুধু অ্যাডমিনদের জন্য!")
            return
            
        chat_id = update.effective_chat.id
        user_to_mute = None
        
        # Check if command is a reply
        if update.message.reply_to_message:
            user_to_mute = update.message.reply_to_message.from_user
        # Check if username is provided
        elif context.args:
            username = context.args[0].replace("@", "")
            try:
                chat_member = context.bot.get_chat_member(chat_id, username)
                user_to_mute = chat_member.user
            except Exception:
                update.message.reply_text("ইউজার পাওয়া যায়নি!")
                return
        else:
            update.message.reply_text("একজন ইউজারকে মিউট করতে তার মেসেজে রিপ্লাই দিন অথবা ইউজারনেম দিন।")
            return
            
        try:
            # Get current warn count
            warn_count = self.db.increment_warn(chat_id, user_to_mute.id)
            
            if warn_count >= 5:
                # Ban user after 5 warnings
                context.bot.ban_chat_member(chat_id, user_to_mute.id)
                self.db.add_banned_user(chat_id, user_to_mute.id)
                update.message.reply_text(
                    f"ইউজার {user_to_mute.first_name} কে 5টি ওয়ার্নিং এর কারণে ব্যান করা হয়েছে।"
                )
            else:
                # Mute for 24 hours
                until_date = int(time.time() + 24 * 60 * 60)
                context.bot.restrict_chat_member(
                    chat_id, 
                    user_to_mute.id,
                    until_date=until_date,
                    permissions=ChatPermissions(
                        can_send_messages=False,
                        can_send_media_messages=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False
                    )
                )
                
                # Add to database
                self.db.add_muted_user(chat_id, user_to_mute.id)
                
                update.message.reply_text(
                    f"ইউজার {user_to_mute.first_name} কে 24 ঘণ্টার জন্য মিউট করা হয়েছে।\n"
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
                self.db.update_group_settings(chat_id, settings)
                query.answer("লিংক ফিল্টার আপডেট করা হয়েছে!")
                
            elif action == 'welcome':
                settings['welcome_msg'] = not settings['welcome_msg']
                self.db.update_group_settings(chat_id, settings)
                query.answer("ওয়েলকাম মেসেজ আপডেট করা হয়েছে!")
                
            elif action == 'service':
                settings['clean_service'] = not settings['clean_service']
                self.db.update_group_settings(chat_id, settings)
                query.answer("সার্ভিস মেসেজ সেটিং আপডেট করা হয়েছে!")
                
            elif action == 'website':
                query.message.reply_text(
                    "দয়া করে আপনার ওয়েবসাইট লিংক পাঠান।\n"
                    "উদাহরণ: https://cinemazbd.com"
                )
                # Store the chat_id for processing the next message
                context.user_data['waiting_for_website'] = chat_id
                query.answer()
                return
            
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
                    InlineKeyboardButton(
                        f"ওয়েবসাইট লিংক: {'✅' if settings.get('website_link') else '❌'}", 
                        callback_data=f"group_website_{chat_id}"
                    )
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.message.edit_reply_markup(reply_markup=reply_markup)

    # Continue in next message due to length... 