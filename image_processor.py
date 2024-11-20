from PIL import Image, ImageDraw, ImageFont
import os

class ImageProcessor:
    def __init__(self):
        self.logo_path = "assets/logo.png"
        self.font_path = "assets/font.ttf"
        
    def add_watermark(self, image_path, text="CinemazBD তে ফ্রী পাওয়া যাচ্ছে"):
        # Open the image
        img = Image.open(image_path)
        
        # Add logo
        logo = Image.open(self.logo_path)
        logo = logo.resize((100, 100))  # Adjust size as needed
        
        # Calculate position for bottom right
        position = (img.width - logo.width - 10, img.height - logo.height - 10)
        
        # Paste logo
        img.paste(logo, position, logo)
        
        # Add text
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(self.font_path, 30)
        
        # Add text above logo
        text_position = (position[0], position[1] - 40)
        draw.text(text_position, text, font=font, fill="white")
        
        return img 