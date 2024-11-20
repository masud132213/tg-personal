from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from PIL import Image, ImageDraw, ImageFont
import os
from image_processor import ImageProcessor
import tempfile

class PosterBot:
    def __init__(self):
        self.token = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
        self.updater = Updater(self.token, use_context=True)
        self.dp = self.updater.dispatcher
        self.image_processor = ImageProcessor()
        
        # Command handlers
        self.dp.add_handler(CommandHandler("start", self.start))
        self.dp.add_handler(MessageHandler(Filters.photo, self.process_image))
        
    def start(self, update, context):
        update.message.reply_text(
            "স্বাগতম! আপনার পোস্টার পাঠান, আমি এটিতে CinemazBD লোগো যুক্ত করে দিব।"
        )
    
    def process_image(self, update, context):
        try:
            # Get the photo file
            photo = update.message.photo[-1]
            file = context.bot.get_file(photo.file_id)
            
            # Create temp directory if it doesn't exist
            if not os.path.exists('temp'):
                os.makedirs('temp')
            
            # Download the image
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg', dir='temp')
            file.download(temp_file.name)
            
            # Process the image
            processed_img = self.image_processor.add_watermark(temp_file.name)
            
            # Save the processed image
            output_path = temp_file.name.replace('.jpg', '_processed.jpg')
            processed_img.save(output_path)
            
            # Send the processed image back
            with open(output_path, 'rb') as photo_file:
                update.message.reply_photo(photo_file)
            
            # Cleanup temp files
            os.unlink(temp_file.name)
            os.unlink(output_path)
            
        except Exception as e:
            update.message.reply_text(f"দুঃখিত! একটি সমস্যা হয়েছে: {str(e)}")

    def run(self):
        self.updater.start_polling()
        self.updater.idle()

if __name__ == '__main__':
    # Create assets directory if it doesn't exist
    if not os.path.exists('assets'):
        os.makedirs('assets')
    
    bot = PosterBot()
    print("Bot is running...")
    bot.run() 