from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

class ImageProcessor:
    def __init__(self):
        self.logo_path = os.path.join('assets', 'logo.png')
        self.font_path = os.path.join('assets', 'font.ttf')
        
    def add_watermark(self, image_path, text="CinemazBD"):
        try:
            # Verify files exist
            if not os.path.exists(self.logo_path):
                raise FileNotFoundError(f"Logo file not found at {self.logo_path}")
            if not os.path.exists(self.font_path):
                raise FileNotFoundError(f"Font file not found at {self.font_path}")
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Input image not found at {image_path}")

            # Open and convert image
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create gradient overlay
            gradient = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(gradient)
            
            # Add vertical gradient at bottom
            height = img.height
            for i in range(height - int(height * 0.5), height):
                alpha = int(255 * (i - (height - int(height * 0.5))) / (int(height * 0.5)))
                draw.line([(0, i), (img.width, i)], fill=(0, 0, 0, alpha))
            
            # Merge gradient with image
            img = Image.alpha_composite(img.convert('RGBA'), gradient)
            
            # Add logo
            logo = Image.open(self.logo_path)
            
            # Make logo bigger (30% of image width)
            logo_width = int(img.width * 0.3)
            logo_height = int(logo.height * (logo_width / logo.width))
            logo = logo.resize((logo_width, logo_height))
            
            # Position logo at bottom center
            position = (int((img.width - logo_width) / 2), img.height - logo_height - 40)
            
            # Add glowing effect to logo
            glow = logo.copy()
            for i in range(10):
                if logo.mode == 'RGBA':
                    img.paste(glow.resize((logo_width + i*2, logo_height + i*2)), 
                            (position[0] - i, position[1] - i), 
                            glow.resize((logo_width + i*2, logo_height + i*2)))
            
            # Paste final logo
            if logo.mode == 'RGBA':
                img.paste(logo, position, logo)
            else:
                img.paste(logo, position)
            
            # Add text with larger size and better styling
            draw = ImageDraw.Draw(img)
            
            # Main text (CinemazBD)
            main_font_size = int(img.width * 0.08)  # Increased size
            main_font = ImageFont.truetype(self.font_path, main_font_size)
            main_text = "CinemazBD"
            main_text_width = draw.textlength(main_text, font=main_font)
            main_text_position = (int((img.width - main_text_width) / 2), position[1] - main_font_size - 20)
            
            # Add dramatic glow effect to main text
            for offset in [(x, y) for x in range(-3, 4) for y in range(-3, 4)]:
                draw.text((main_text_position[0] + offset[0], main_text_position[1] + offset[1]),
                         main_text, font=main_font, fill=(255, 165, 0, 50))  # Orange glow
            
            # Main text with gradient
            for i in range(main_font_size):
                opacity = int(255 * (1 - i/main_font_size))
                color = (255, min(255, 165 + i), min(255, i), opacity)
                draw.text((main_text_position[0], main_text_position[1] + i/2),
                         main_text, font=main_font, fill=color)
            
            # Subtitle text
            sub_font_size = int(img.width * 0.04)  # Increased size
            sub_font = ImageFont.truetype(self.font_path, sub_font_size)
            sub_text = "আপনার পছন্দের সব মুভি/সিরিজ"
            sub_text_width = draw.textlength(sub_text, font=sub_font)
            sub_text_position = (int((img.width - sub_text_width) / 2), main_text_position[1] - sub_font_size - 10)
            
            # Add glowing effect to subtitle
            for offset in [(x, y) for x in range(-2, 3) for y in range(-2, 3)]:
                draw.text((sub_text_position[0] + offset[0], sub_text_position[1] + offset[1]),
                         sub_text, font=sub_font, fill=(0, 0, 0, 80))
            draw.text(sub_text_position, sub_text, font=sub_font, fill=(255, 255, 255, 255))
            
            return img.convert('RGB')
            
        except Exception as e:
            raise Exception(f"Image processing error: {str(e)}")

    def apply_template(self, image_path, template_name="default"):
        templates = {
            "default": self.add_watermark,
            "movie": self.movie_template,
            "series": self.series_template,
            "minimal": self.minimal_template
        }
        
        if template_name in templates:
            return templates[template_name](image_path)
        return self.add_watermark(image_path)
    
    def movie_template(self, image_path):
        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Add cinematic gradient
            gradient = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(gradient)
            
            # Vertical gradient
            for i in range(img.height):
                alpha = int(255 * (0.3 if i < img.height/2 else (i - img.height/2)/(img.height/2)))
                draw.line([(0, i), (img.width, i)], fill=(0, 0, 0, alpha))
            
            img = Image.alpha_composite(img.convert('RGBA'), gradient)
            
            # Add watermark with special styling
            return self.add_watermark(img)
            
        except Exception as e:
            raise Exception(f"Template error: {str(e)}")
    
    def series_template(self, image_path):
        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Add TV series style overlay
            gradient = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(gradient)
            
            # Create diagonal gradient
            for i in range(img.width):
                alpha = int(255 * (i/img.width) * 0.7)
                draw.line([(i, 0), (i, img.height)], fill=(0, 0, 0, alpha))
            
            img = Image.alpha_composite(img.convert('RGBA'), gradient)
            
            # Add watermark with special styling
            return self.add_watermark(img)
            
        except Exception as e:
            raise Exception(f"Template error: {str(e)}")
    
    def minimal_template(self, image_path):
        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Add subtle gradient
            gradient = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(gradient)
            
            # Bottom gradient only
            for i in range(img.height - int(img.height * 0.3), img.height):
                alpha = int(255 * (i - (img.height - int(img.height * 0.3))) / (int(img.height * 0.3)) * 0.5)
                draw.line([(0, i), (img.width, i)], fill=(0, 0, 0, alpha))
            
            img = Image.alpha_composite(img.convert('RGBA'), gradient)
            
            # Add watermark with minimal styling
            return self.add_watermark(img)
            
        except Exception as e:
            raise Exception(f"Template error: {str(e)}")