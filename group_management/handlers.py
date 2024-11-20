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
        dispatcher.add_handler(CallbackQueryHandler(self.handle_callback_query, pattern='^group_'))
        dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, self.welcome_new_member))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))

    def group_settings(self, update, context):
        """Handle /group command"""
        if not self.is_admin(update):
            update.message.reply_text("এই কমান্ড শুধু অ্যাডমিনদের জন্য!")
            return
            
        chat_id = update.effective_chat.id
        
        # Check bot permissions
        has_permissions, message = self.check_bot_permissions(chat_id, context)
        if not has_permissions:
            update.message.reply_text(message)
            return
            
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
            print(f"New member in chat: {chat_id}")
            
            # Get group settings
            settings = self.db.get_group_settings(chat_id)
            print(f"Group settings: {settings}")
            
            # Check if welcome message is enabled
            if not settings.get('welcome_msg', True):  # Default to True
                print("Welcome message is disabled")
                return
                
            # Get new members
            new_members = update.message.new_chat_members
            print(f"New members: {new_members}")
            
            for new_member in new_members:
                # Skip if member is a bot
                if new_member.is_bot:
                    print("New member is a bot, skipping")
                    continue
                    
                print(f"Welcoming user: {new_member.first_name}")
                
                # Get website link from settings
                website_link = settings.get('website_link', 'https://t.me/cinemazbd_pm')
                
                # Get welcome message and buttons
                message, buttons = self.welcome.get_random_template(new_member.first_name, website_link)
                
                # Create keyboard markup
                keyboard = []
                if buttons:
                    for button in buttons:
                        keyboard.append([
                            InlineKeyboardButton(
                                text=button['text'],
                                url=button['url']
                            )
                        ])
                reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                
                try:
                    # Send welcome message
                    welcome_msg = context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        reply_markup=reply_markup,
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
                    print("Welcome message sent successfully")
                    
                    # Delete service message if enabled
                    if settings.get('clean_service', True):  # Default to True
                        try:
                            update.message.delete()
                            print("Service message deleted")
                        except Exception as e:
                            print(f"Error deleting service message: {e}")
                    
                    # Schedule welcome message deletion
                    if welcome_msg:
                        context.job_queue.run_once(
                            lambda ctx: self.delete_message_safe(chat_id, welcome_msg.message_id, context.bot),
                            3
                        )
                        print("Message deletion scheduled")
                        
                except Exception as e:
                    print(f"Error sending welcome message: {e}")
                    
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
        user_id = update.message.from_user.id
        
        # Check if waiting for website link
        if context.user_data.get('waiting_for_website'):
            if not self.is_admin(update):
                update.message.reply_text("এই কমান্ড শুধু অ্যাডমিনদের জন্য!")
                return
                
            website_link = update.message.text
            if not website_link.startswith(('http://', 'https://')):
                update.message.reply_text("দয়া করে একটি সঠিক লিংক দিন (http:// বা https:// দিয়ে শুরু হওয়া)")
                return
                
            settings = self.db.get_group_settings(chat_id)
            settings['website_link'] = website_link
            self.db.update_group_settings(chat_id, settings)
            
            update.message.reply_text("ওয়েবসাইট লিংক সেট করা হয়েছে!")
            del context.user_data['waiting_for_website']
            return
            
        settings = self.db.get_group_settings(chat_id)
        
        # Skip link filter for admins and owners
        if self.is_admin(update) or user_id in OWNER_IDS:
            return
            
        # Only check link filter in groups
        if update.effective_chat.type not in ['group', 'supergroup']:
            return
            
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
                        lambda _: self.delete_message_safe(chat_id, msg.message_id, context.bot),
                        3
                    )
                    return
                except Exception as e:
                    print(f"Error in link filter: {e}")

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
            update.message.reply_text(f"মিউট করত সমস্যা হয়েছে: {str(e)}")

    def button_callback(self, query, chat_id, action, settings):
        """Handle button callbacks"""
        try:
            if action == 'link':
                settings['link_filter'] = not settings['link_filter']
                self.db.update_group_settings(chat_id, settings)
                return "লিংক ফিল্টার আপডেট করা হয়েছে!"
                
            elif action == 'welcome':
                settings['welcome_msg'] = not settings['welcome_msg']
                self.db.update_group_settings(chat_id, settings)
                return "ওয়েলকাম মেসেজ আপডেট করা হয়েছে!"
                
            elif action == 'service':
                settings['clean_service'] = not settings['clean_service']
                self.db.update_group_settings(chat_id, settings)
                return "সার্ভিস মেসেজ সেটিং আপডেট করা হয়েছে!"
                
            elif action == 'website':
                query.message.reply_text(
                    "দয়া করে আপনার ওয়েবসাইট লিংক পাঠান।\n"
                    "উদাহরণ: https://t.me/cinemazbd_pm"
                )
                return None
                
            elif action == 'banword':
                query.message.reply_text(
                    "দয়া করে ব্যান করার জন্য শব্দ লিখুন।\n"
                    "একাধিক শব্দ কমা দিয়ে আলাদা করুন।"
                )
                return None
                
            elif action == 'banuser':
                banned_users = settings.get('banned_users', [])
                user_list = "\n".join([f"• {uid}" for uid in banned_users]) or "কোন ইউজার ব্যান করা হয়নি"
                query.message.reply_text(f"ব্যান করা ইউজারের তালিকা:\n{user_list}")
                return None
                
            elif action == 'mute':
                muted_users = settings.get('muted_users', [])
                user_list = "\n".join([f"• {uid}" for uid in muted_users]) or "কোন ইউজার মিউট করা হয়নি"
                query.message.reply_text(f"মিউট করা ইউজারের তালিকা:\n{user_list}")
                return None
                
        except Exception as e:
            print(f"Error in button callback: {e}")
            return "একটি সমস্যা হয়েছে!"

    def handle_callback_query(self, update, context):
        """Handle callback queries"""
        query = update.callback_query
        
        if not query.data.startswith('group_'):
            return
            
        parts = query.data.split('_')
        if len(parts) < 3:
            return
            
        action = parts[1]
        chat_id = int(parts[2])
        
        # Check if user is admin
        if not self.is_admin(query):
            query.answer("এই কমান্ড শুধু অ্যাডমিনদের জন্য!")
            return
            
        settings = self.db.get_group_settings(chat_id)
        
        # Handle the button press
        result = self.button_callback(query, chat_id, action, settings)
        if result:
            query.answer(result)
        
        # Update keyboard if needed
        if action not in ['website', 'banword']:
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

    def check_bot_permissions(self, chat_id, context):
        """Check if bot has all required permissions"""
        try:
            bot_member = context.bot.get_chat_member(chat_id, context.bot.id)
            
            # Check if bot is admin
            if bot_member.status not in ['administrator', 'creator']:
                return (False, "বট কে অ্যাডমিন করা হয়নি!")
            
            # Get bot permissions
            permissions = bot_member.can_delete_messages, bot_member.can_restrict_members
            
            if not all(permissions):
                missing = []
                if not bot_member.can_delete_messages:
                    missing.append("Delete messages")
                if not bot_member.can_restrict_members:
                    missing.append("Ban/Mute users")
                
                return (False, f"বট এর নিম্নলিখিত পারমিশন নেই:\n" + "\n".join(f"• {p}" for p in missing))
            
            return (True, "সব পারমিশন আছে!")
            
        except Exception as e:
            print(f"Error checking permissions: {e}")
            return (False, "পারমিশন চেক করতে সমস্যা হয়েছে!")

    # Continue in next message due to length... 