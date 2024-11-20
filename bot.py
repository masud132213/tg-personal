from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image, ImageDraw, ImageFont
import os, tempfile, requests, json
from image_processor import ImageProcessor
import psutil, platform
from datetime import datetime
from template_generator.generator import TemplateGenerator

OWNER_IDS = [7202314047, 1826754085]
AUTHORIZED_CHATS = [-1002385279104]

class PosterBot:
    def __init__(self):
        self.token = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
        self.tmdb_api_key = os.environ.get("TMDB_API_KEY", "YOUR_TMDB_API_KEY")
        self.updater = Updater(self.token, use_context=True)
        self.dp = self.updater.dispatcher
        self.image_processor = ImageProcessor()
        self.user_states = {}
        self.template_generator = TemplateGenerator()
        
        # Setup handlers
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup all command handlers"""
        self.dp.add_handler(CommandHandler("start", self.start))
        self.dp.add_handler(CommandHandler("stats", self.stats))
        self.dp.add_handler(CommandHandler("tm", self.search_movie))
        self.dp.add_handler(CommandHandler("tt", self.search_tv))
        self.dp.add_handler(CommandHandler("i", self.process_last_image))
        self.dp.add_handler(CommandHandler("itemp", self.process_last_image_template))
        self.dp.add_handler(CommandHandler("t", self.start_template))
        self.dp.add_handler(MessageHandler(Filters.photo, self.save_image))
        self.dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.process_image_url))
        self.dp.add_handler(CallbackQueryHandler(self.handle_template_callback))
        
        # Update start message
        self.start_message = (
            "স্বাগতম! আমি আপনার পোস্টার এডিট করতে পারি।\n\n"
            "কমান্ডসমূহ:\n"
            "/i - সর্বশেষ ছবিতে লোগো যোগ করুন\n"
            "/itemp - টেমপ্লেট সহ এডিট করুন\n"
            "/t - নতুন টেমপ্লেট তৈরি করুন\n"
            "/tm movie_name - মুভি সার্চ করুন\n"
            "/tt series_name - টিভি সিরিজ সার্চ করুন\n"
            "/stats - সার্ভার স্ট্যাটস দেখুন"
        )

    def start(self, update, context):
        update.message.reply_text(self.start_message)

    def stats(self, update, context):
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        uptime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        stats_text = (
            f"🖥 সার্ভার সট্যাটস:\n\n"
            f"CPU: {cpu}%\n"
            f"Memory: {memory}%\n"
            f"Disk: {disk}%\n"
            f"OS: {platform.system()}\n"
            f"Uptime: {uptime}"
        )
        update.message.reply_text(stats_text)

    def save_image(self, update, context):
        """Save image for processing"""
        chat_id = update.effective_chat.id
        user_id = update.message.from_user.id
        
        # Only allow in private chat with sudo users
        if update.effective_chat.type == 'private' and user_id in OWNER_IDS:
            photo = update.message.photo[-1]
            self.user_states[user_id] = {
                'last_photo': photo,
                'message_id': update.message.message_id
            }
            
            # Check if user is in template generation process
            if hasattr(self.template_generator, 'current_state') and user_id in self.template_generator.current_state:
                # Continue with template generation
                state = self.template_generator.current_state[user_id]
                if state['step'] == 'title':
                    update.message.reply_text("টাইটেল লিখুন 🎬")
            else:
                # Normal image save message
                update.message.reply_text(
                    "ছবি সেভ করা হয়েছে। এডিট করতে /i অথবা টেমপ্লেট ব্যবহার করতে /itemp কমান্ড ব্যবহার করুন।"
                )

    def process_image(self, update, context, photo):
        try:
            # Download the photo
            file = context.bot.get_file(photo.file_id)
            
            # Create temp directory if it doesn't exist
            if not os.path.exists('temp'):
                os.makedirs('temp')
            
            # Download and save the image
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg', dir='temp')
            file.download(temp_file.name)
            
            # Process the image
            processed_img = self.image_processor.add_watermark(temp_file.name)
            output_path = temp_file.name.replace('.jpg', '_processed.jpg')
            processed_img.save(output_path)
            
            # Send the processed image
            with open(output_path, 'rb') as photo_file:
                update.message.reply_photo(photo_file)
            
            # Cleanup
            os.unlink(temp_file.name)
            os.unlink(output_path)
            
        except Exception as e:
            update.message.reply_text(f"ছবি প্রসেস করতে সমস্যা হয়েছে: {str(e)}")

    def process_last_image(self, update, context):
        # Check if admin/owner
        if not self.is_admin_or_owner(update):
            update.message.reply_text("এই কমান্ড শুধু অ্যাডমিনদের জন্য!")
            return
            
        user_id = update.message.from_user.id
        if user_id not in self.user_states:
            update.message.reply_text("দয়া করে আগে একটি ছবি পাঠান।")
            return
        
        try:
            photo = self.user_states[user_id]['last_photo']
            self.process_image(update, context, photo)
        except Exception as e:
            update.message.reply_text(f"দুঃখিত! একটি সমস্যা হয়েছে: {str(e)}")

    def process_image_url(self, update, context):
        text = update.message.text
        if text.startswith(('http://', 'https://')) and any(ext in text.lower() for ext in ['.jpg', '.jpeg', '.png']):
            try:
                response = requests.get(text)
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                temp_file.write(response.content)
                temp_file.close()
                
                processed_img = self.image_processor.add_watermark(temp_file.name)
                output_path = temp_file.name.replace('.jpg', '_processed.jpg')
                processed_img.save(output_path)
                
                with open(output_path, 'rb') as photo_file:
                    update.message.reply_photo(photo_file)
                
                os.unlink(temp_file.name)
                os.unlink(output_path)
            except Exception as e:
                update.message.reply_text(f"ছবি প্রসেস করতে সমস্যা হয়েছে: {str(e)}")

    def search_movie(self, update, context):
        if not self.is_authorized(update):
            update.message.reply_text("আপনি এই কমান্ড ব্যবহার করতে অনুমোদিত নন।")
            return

        query = ' '.join(context.args)
        if not query:
            update.message.reply_text("দয়া করে একটি মুভির নাম লিখুন।")
            return
        
        url = f"https://api.themoviedb.org/3/search/movie"
        params = {
            'api_key': self.tmdb_api_key,
            'query': query,
            'language': 'en-US',
            'page': 1
        }
        
        try:
            response = requests.get(url, params=params)
            results = response.json()['results'][:5]
            
            if not results:
                update.message.reply_text("কোন মুভি পাওয়া যায়নি।")
                return
            
            keyboard = []
            for movie in results:
                year = movie.get('release_date', '')[:4]
                title = f"{movie['title']} ({year})" if year else movie['title']
                callback_data = f"movie_{movie['id']}"
                keyboard.append([InlineKeyboardButton(title, callback_data=callback_data)])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("নিচের মুভিগুলো থেকে একটি সিলেক্ট করুন:", reply_markup=reply_markup)
        
        except Exception as e:
            update.message.reply_text(f"সার্চ করতে সমস্যা হয়েছে: {str(e)}")

    def button_callback(self, update, context):
        query = update.callback_query
        data = query.data
        
        if data.startswith('template_'):
            template_type = data.split('_')[1]
            user_id = query.from_user.id
            
            if user_id not in self.user_states:
                query.message.reply_text("দয়া করে আগে একটি ছবি পাঠান।")
                return
            
            try:
                photo = self.user_states[user_id]['last_photo']
                file = context.bot.get_file(photo.file_id)
                
                # Create temp directory if it doesn't exist
                if not os.path.exists('temp'):
                    os.makedirs('temp')
                
                # Download and save the image
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg', dir='temp')
                file.download(temp_file.name)
                
                # Process the image with selected template
                processed_img = self.image_processor.apply_template(temp_file.name, template_type)
                output_path = temp_file.name.replace('.jpg', '_processed.jpg')
                processed_img.save(output_path)
                
                # Send the processed image
                with open(output_path, 'rb') as photo_file:
                    query.message.reply_photo(photo_file)
                
                # Cleanup
                os.unlink(temp_file.name)
                os.unlink(output_path)
                
                # Delete the template selection message
                query.message.delete()
                
            except Exception as e:
                query.message.reply_text(f"টেমপ্লেট প্রসেস করতে সমস্যা হয়েছে: {str(e)}")
            
            finally:
                query.answer()
            
        elif data.startswith('movie_'):
            movie_id = data.split('_')[1]
            self.show_movie_details(query, movie_id)
        elif data.startswith('tv_'):
            tv_id = data.split('_')[1]
            self.show_tv_details(query, tv_id)

    def show_movie_details(self, query, movie_id):
        url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        params = {
            'api_key': self.tmdb_api_key,
            'language': 'en-US'
        }
        
        try:
            response = requests.get(url, params=params)
            movie = response.json()
            
            details = (
                f"🎬 {movie['title']}\n\n"
                f"📅 Year: {movie.get('release_date', 'N/A')[:4]}\n"
                f"🌟 Rating: {movie.get('vote_average', 'N/A')}/10\n"
                f"🎭 Genres: {', '.join(genre['name'] for genre in movie.get('genres', []))}\n"
                f"🌍 Country: {movie.get('production_countries', [{}])[0].get('name', 'N/A')}\n\n"
                f"📝 Overview: {movie.get('overview', 'N/A')}"
            )
            
            if movie.get('poster_path'):
                poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
                query.message.reply_photo(poster_url, caption=details)
            else:
                query.message.reply_text(details)
            
        except Exception as e:
            query.message.reply_text(f"বিস্তা���িত দেখাতে সমস্যা হয়েছে: {str(e)}")

    def process_last_image_template(self, update, context):
        # Check if admin/owner
        if not self.is_admin_or_owner(update):
            update.message.reply_text("এই কমান্ড শুধু অ্যাডমিনদের জন্য!")
            return
            
        user_id = update.message.from_user.id
        if user_id not in self.user_states:
            update.message.reply_text("দয়া করে আগে একটি ছবি পাঠান।")
            return
        
        # Create template selection keyboard
        keyboard = [
            [
                InlineKeyboardButton("মুভি টেমপ্লেট", callback_data="template_movie"),
                InlineKeyboardButton("সিরিজ টেমপ্লেট", callback_data="template_series")
            ],
            [InlineKeyboardButton("মিনিমাল টেমপ্লেট", callback_data="template_minimal")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(
            "টেমপ্লেট সিলেক্ট করুন:",
            reply_markup=reply_markup
        )

    def search_tv(self, update, context):
        if not self.is_authorized(update):
            update.message.reply_text("আপনি এই কমান্ড ব্যবহার করতে অনুমোদিত নন।")
            return
        
        query = ' '.join(context.args)
        if not query:
            update.message.reply_text("দয়া করে একটি টিভি সিরিজের নাম লিখুন।")
            return
        
        url = f"https://api.themoviedb.org/3/search/tv"
        params = {
            'api_key': self.tmdb_api_key,
            'query': query,
            'language': 'en-US',
            'page': 1
        }
        
        try:
            response = requests.get(url, params=params)
            results = response.json()['results'][:5]
            
            if not results:
                update.message.reply_text("কোন টিভি সিরিজ পাওয়া যায়নি।")
                return
            
            keyboard = []
            for show in results:
                callback_data = f"tv_{show['id']}"
                keyboard.append([InlineKeyboardButton(show['name'], callback_data=callback_data)])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("নিচের সিরিজগুলো থেকে একটি সিলেক্ট করুন:", reply_markup=reply_markup)
        
        except Exception as e:
            update.message.reply_text(f"সার্চ করতে সমস্যা হয়েছে: {str(e)}")

    def show_tv_details(self, query, tv_id):
        url = f"https://api.themoviedb.org/3/tv/{tv_id}"
        params = {
            'api_key': self.tmdb_api_key,
            'language': 'en-US'
        }
        
        try:
            response = requests.get(url, params=params)
            show = response.json()
            
            details = (
                f"📺 {show['name']}\n\n"
                f"📅 First Air: {show.get('first_air_date', 'N/A')[:4]}\n"
                f"🌟 Rating: {show.get('vote_average', 'N/A')}/10\n"
                f"🎭 Genres: {', '.join(genre['name'] for genre in show.get('genres', []))}\n"
                f"📺 Seasons: {show.get('number_of_seasons', 'N/A')}\n"
                f"🌍 Country: {show.get('origin_country', ['N/A'])[0]}\n\n"
                f"📝 Overview: {show.get('overview', 'N/A')}"
            )
            
            if show.get('poster_path'):
                poster_url = f"https://image.tmdb.org/t/p/w500{show['poster_path']}"
                query.message.reply_photo(poster_url, caption=details)
            else:
                query.message.reply_text(details)
            
        except Exception as e:
            query.message.reply_text(f"বিস্তারিত দেখাতে সমস্যা হয়েছে: {str(e)}")

    def is_authorized(self, update):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if user_id in OWNER_IDS:
            return True
        if chat_id in AUTHORIZED_CHATS:
            return True
        return False

    def is_admin_or_owner(self, update):
        """Check if user is admin or owner"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Check if user is owner
        if user_id in OWNER_IDS:
            return True
            
        # Check if in group and user is admin
        try:
            chat_member = update.effective_chat.get_member(user_id)
            return chat_member.status in ['creator', 'administrator']
        except Exception:
            return False

    def start_template(self, update, context):
        """Start template generation process"""
        user_id = update.effective_user.id
        
        # Check if authorized
        if not self.is_authorized(update):
            update.message.reply_text("আপনি এই কমান্ড ব্যবহার করতে অনুমোদিত নন।")
            return
            
        response = self.template_generator.start_template(user_id)
        update.message.reply_text(response)
        
    def handle_template_callback(self, update, context):
        """Handle template selection"""
        query = update.callback_query
        data = query.data
        
        if data.startswith('template_'):
            _, template_num, user_id = data.split('_')
            user_id = int(user_id)
            
            if user_id != update.effective_user.id:
                query.answer("এই টেমপ্লেট আপনার জন্য নয়!")
                return
                
            # Generate template
            result = self.template_generator.generate_template(
                template_num,
                user_id,
                self.user_states[user_id]['last_photo']
            )
            
            if result:
                img, button_text, link = result
                
                # Save temporary image
                temp_path = f"temp/template_{user_id}.jpg"
                img.save(temp_path)
                
                # Create button
                keyboard = [[InlineKeyboardButton(button_text, url=link)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send image with button
                with open(temp_path, 'rb') as photo:
                    query.message.reply_photo(
                        photo,
                        reply_markup=reply_markup
                    )
                    
                # Cleanup
                os.remove(temp_path)
                
                # Clear user state
                del self.template_generator.current_state[user_id]
                
            query.answer()
            query.message.delete()

    def run(self):
        # Start the bot
        self.updater.start_polling()
        print("Bot is running...")

        # Start health check server
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class HealthCheckHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"OK")
            
            def log_message(self, format, *args):
                pass

        def run_health_server():
            try:
                server = HTTPServer(('', 8080), HealthCheckHandler)
                print("Health check server running on port 8080")
                server.serve_forever()
            except Exception as e:
                print(f"Health server error: {e}")

        import threading
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()

        # Keep the main thread running
        self.updater.idle()

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('assets', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    
    bot = PosterBot()
    bot.run() 