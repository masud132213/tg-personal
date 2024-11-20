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
            
            # Add stronger vertical gradient at bottom
            height = img.height
            for i in range(height - int(height * 0.4), height):
                alpha = int(255 * (i - (height - int(height * 0.4))) / (int(height * 0.4)))
                draw.line([(0, i), (img.width, i)], fill=(0, 0, 0, min(alpha + 50, 255)))
            
            # Merge gradient with image
            img = Image.alpha_composite(img.convert('RGBA'), gradient)
            
            # Add logo
            logo = Image.open(self.logo_path)
            
            # Make logo bigger (25% of image width)
            logo_width = int(img.width * 0.25)
            logo_height = int(logo.height * (logo_width / logo.width))
            logo = logo.resize((logo_width, logo_height))
            
            # Position logo at bottom center
            position = (int((img.width - logo_width) / 2), img.height - logo_height - 60)
            
            # Create background for logo
            bg = Image.new('RGBA', (logo_width + 20, logo_height + 20), (0, 0, 0, 180))
            img.paste(bg, (position[0] - 10, position[1] - 10), bg)
            
            # Paste logo
            if logo.mode == 'RGBA':
                img.paste(logo, position, logo)
            else:
                img.paste(logo, position)
            
            # Add text with larger size and better styling
            draw = ImageDraw.Draw(img)
            
            # Main text (CinemazBD)
            main_font_size = int(img.width * 0.1)  # Increased size more
            main_font = ImageFont.truetype(self.font_path, main_font_size)
            main_text = "CinemazBD"
            main_text_width = draw.textlength(main_text, font=main_font)
            main_text_position = (int((img.width - main_text_width) / 2), position[1] - main_font_size - 30)
            
            # Add strong shadow/glow effect
            shadow_color = (0, 0, 0, 255)
            glow_color = (255, 140, 0, 150)  # Orange glow
            
            # Add black shadow first
            for offset in [(x, y) for x in range(-3, 4, 2) for y in range(-3, 4, 2)]:
                draw.text((main_text_position[0] + offset[0], main_text_position[1] + offset[1]),
                         main_text, font=main_font, fill=shadow_color)
            
            # Add glow effect
            for offset in [(x, y) for x in range(-2, 3) for y in range(-2, 3)]:
                draw.text((main_text_position[0] + offset[0], main_text_position[1] + offset[1]),
                         main_text, font=main_font, fill=glow_color)
            
            # Main text in white
            draw.text(main_text_position, main_text, font=main_font, fill=(255, 255, 255, 255))
            
            # Subtitle text
            sub_font_size = int(img.width * 0.045)  # Slightly increased
            sub_font = ImageFont.truetype(self.font_path, sub_font_size)
            sub_text = "আপনার পছন্দের সব মুভি / সিরিজ"
            sub_text_width = draw.textlength(sub_text, font=sub_font)
            sub_text_position = (int((img.width - sub_text_width) / 2), main_text_position[1] - sub_font_size - 10)
            
            # Add shadow to subtitle
            for offset in [(x, y) for x in range(-2, 3) for y in range(-2, 3)]:
                draw.text((sub_text_position[0] + offset[0], sub_text_position[1] + offset[1]),
                         sub_text, font=sub_font, fill=(0, 0, 0, 100))
            draw.text(sub_text_position, sub_text, font=sub_font, fill=(255, 255, 255, 255))
            
            return img.convert('RGB')
            
        except Exception as e:
            raise Exception(f"Image processing error: {str(e)}")

    def apply_template(self, image_path, template_name="default"):
        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            if template_name == "movie":
                # Add cinematic gradient
                gradient = Image.new('RGBA', img.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(gradient)
                
                # Vertical gradient
                for i in range(img.height):
                    alpha = int(255 * (0.3 if i < img.height/2 else (i - img.height/2)/(img.height/2)))
                    draw.line([(0, i), (img.width, i)], fill=(0, 0, 0, alpha))
                
                img = Image.alpha_composite(img.convert('RGBA'), gradient)
                
            elif template_name == "series":
                # Add TV series style overlay
                gradient = Image.new('RGBA', img.size, (0, 0, 0, 0))
                draw = ImageDraw.Draw(gradient)
                
                # Diagonal gradient
                for i in range(img.width):
                    alpha = int(255 * (i/img.width) * 0.7)
                    draw.line([(i, 0), (i, img.height)], fill=(0, 0, 0, alpha))
                
                img = Image.alpha_composite(img.convert('RGBA'), gradient)
            
            # Save temporary image
            temp_path = image_path.replace('.jpg', '_temp.jpg')
            img.convert('RGB').save(temp_path)
            
            # Add watermark
            result = self.add_watermark(temp_path)
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return result
            
        except Exception as e:
            raise Exception(f"Template error: {str(e)}")