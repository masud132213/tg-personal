from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image, ImageDraw, ImageFont
import os, tempfile, requests, json
from image_processor import ImageProcessor
import psutil, platform
from datetime import datetime

class PosterBot:
    def __init__(self):
        self.token = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
        self.tmdb_api_key = os.environ.get("TMDB_API_KEY", "YOUR_TMDB_API_KEY")
        self.updater = Updater(self.token, use_context=True)
        self.dp = self.updater.dispatcher
        self.image_processor = ImageProcessor()
        self.user_states = {}  # Store user states
        
        # Command handlers
        self.dp.add_handler(CommandHandler("start", self.start))
        self.dp.add_handler(CommandHandler("stats", self.stats))
        self.dp.add_handler(CommandHandler("tm", self.search_movie))
        self.dp.add_handler(CommandHandler("tt", self.search_tv))
        self.dp.add_handler(CommandHandler("i", self.process_last_image))
        self.dp.add_handler(CommandHandler("itemp", self.process_last_image_template))
        self.dp.add_handler(MessageHandler(Filters.photo, self.save_image))
        self.dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.process_image_url))
        self.dp.add_handler(CallbackQueryHandler(self.button_callback))
        
    def start(self, update, context):
        update.message.reply_text(
            "স্বাগতম! আমি আপনার পোস্টার এডিট করতে পারি।\n\n"
            "কমান্ডসমূহ:\n"
            "/i - সর্বশেষ ছবিতে লোগো যোগ করুন\n"
            "/itemp - টেমপ্লেট সহ এডিট করুন\n"
            "/tm movie_name - মুভি সার্চ করুন\n"
            "/tt series_name - টিভি সিরিজ সার্চ করুন\n"
            "/stats - সার্ভার স্ট্যাটস দেখুন"
        )

    def stats(self, update, context):
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        uptime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        stats_text = (
            f"🖥 সার্ভার স���ট্যাটস:\n\n"
            f"CPU: {cpu}%\n"
            f"Memory: {memory}%\n"
            f"Disk: {disk}%\n"
            f"OS: {platform.system()}\n"
            f"Uptime: {uptime}"
        )
        update.message.reply_text(stats_text)

    def save_image(self, update, context):
        user_id = update.message.from_user.id
        photo = update.message.photo[-1]
        self.user_states[user_id] = {
            'last_photo': photo,
            'message_id': update.message.message_id
        }
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
                callback_data = f"movie_{movie['id']}"
                keyboard.append([InlineKeyboardButton(movie['title'], callback_data=callback_data)])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("নিচের মুভিগুলো থেকে একটি সিলেক্ট করুন:", reply_markup=reply_markup)
        
        except Exception as e:
            update.message.reply_text(f"সার্চ করতে সমস্যা হয়েছে: {str(e)}")

    def button_callback(self, update, context):
        query = update.callback_query
        data = query.data
        
        if data.startswith('movie_'):
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
            query.message.reply_text(f"বিস্তারিত দেখাতে সমস্যা হয়েছে: {str(e)}")

    def process_last_image_template(self, update, context):
        # Will implement template processing later
        update.message.reply_text("টেমপ্লেট ফিচার শীঘ্রই আসছে!")

    def run(self):
        # Start the bot first
        self.updater.start_polling()
        print("Bot is running...")

        # Then start health check server
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class HealthCheckHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"OK")
            
            def log_message(self, format, *args):
                # Suppress logging
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