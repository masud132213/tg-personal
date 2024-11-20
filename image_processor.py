from PIL import Image, ImageDraw, ImageFont
import os

class ImageProcessor:
    def __init__(self):
        self.logo_path = os.path.join('assets', 'logo.png')
        self.font_path = os.path.join('assets', 'font.ttf')
        
    def add_watermark(self, image_path, text="CinemazBD তে ফ্রী পাওয়া যাচ্ছে"):
        try:
            # Verify files exist
            if not os.path.exists(self.logo_path):
                raise FileNotFoundError(f"Logo file not found at {self.logo_path}")
            if not os.path.exists(self.font_path):
                raise FileNotFoundError(f"Font file not found at {self.font_path}")
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Input image not found at {image_path}")

            # Open the image
            img = Image.open(image_path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Add logo
            logo = Image.open(self.logo_path)
            
            # Calculate logo size (10% of image width)
            logo_width = int(img.width * 0.1)
            logo_height = int(logo.height * (logo_width / logo.width))
            logo = logo.resize((logo_width, logo_height))
            
            # Calculate position for bottom right
            position = (img.width - logo_width - 10, img.height - logo_height - 10)
            
            # If logo has transparency
            if logo.mode == 'RGBA':
                img.paste(logo, position, logo)
            else:
                img.paste(logo, position)
            
            # Add text
            draw = ImageDraw.Draw(img)
            
            # Calculate font size (3% of image width)
            font_size = int(img.width * 0.03)
            font = ImageFont.truetype(self.font_path, font_size)
            
            # Add text above logo
            text_position = (position[0], position[1] - font_size - 5)
            
            # Add white text with black outline for better visibility
            for offset in [(1,1), (-1,-1), (1,-1), (-1,1)]:
                draw.text((text_position[0]+offset[0], text_position[1]+offset[1]), 
                         text, font=font, fill="black")
            draw.text(text_position, text, font=font, fill="white")
            
            return img
            
        except Exception as e:
            raise Exception(f"Image processing error: {str(e)}")