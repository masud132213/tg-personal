from PIL import Image, ImageDraw, ImageFont
import os

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

            # Open the image
            img = Image.open(image_path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Add logo
            logo = Image.open(self.logo_path)
            
            # Calculate logo size (20% of image width)
            logo_width = int(img.width * 0.2)
            logo_height = int(logo.height * (logo_width / logo.width))
            logo = logo.resize((logo_width, logo_height))
            
            # Calculate position for bottom center
            position = (int((img.width - logo_width) / 2), img.height - logo_height - 20)
            
            # Create a semi-transparent background for logo
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            bg_box = (position[0], position[1], position[0] + logo_width, position[1] + logo_height)
            overlay_draw.rectangle(bg_box, fill=(0, 0, 0, 128))
            
            # Paste overlay
            img = Image.alpha_composite(img.convert('RGBA'), overlay)
            
            # Paste logo
            if logo.mode == 'RGBA':
                img.paste(logo, position, logo)
            else:
                img.paste(logo, position)
            
            # Add text
            draw = ImageDraw.Draw(img)
            
            # Main text (CinemazBD)
            main_font_size = int(img.width * 0.05)
            main_font = ImageFont.truetype(self.font_path, main_font_size)
            main_text = "CinemazBD"
            main_text_width = draw.textlength(main_text, font=main_font)
            main_text_position = (int((img.width - main_text_width) / 2), position[1] - main_font_size - 10)
            
            # Add glow effect to main text
            for offset in [(x, y) for x in range(-2, 3) for y in range(-2, 3)]:
                draw.text((main_text_position[0] + offset[0], main_text_position[1] + offset[1]),
                         main_text, font=main_font, fill=(0, 0, 0, 100))
            draw.text(main_text_position, main_text, font=main_font, fill="white")
            
            # Subtitle text
            sub_font_size = int(img.width * 0.03)
            sub_font = ImageFont.truetype(self.font_path, sub_font_size)
            sub_text = "আপনার পছন্দের সব মুভি/সিরিজ"
            sub_text_width = draw.textlength(sub_text, font=sub_font)
            sub_text_position = (int((img.width - sub_text_width) / 2), main_text_position[1] - sub_font_size - 5)
            
            # Add subtitle with glow
            for offset in [(x, y) for x in range(-1, 2) for y in range(-1, 2)]:
                draw.text((sub_text_position[0] + offset[0], sub_text_position[1] + offset[1]),
                         sub_text, font=sub_font, fill=(0, 0, 0, 100))
            draw.text(sub_text_position, sub_text, font=sub_font, fill="white")
            
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
                
            # Add gradient overlay
            gradient = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(gradient)
            for i in range(img.height - int(img.height * 0.4), img.height):
                alpha = int(255 * (i - (img.height - int(img.height * 0.4))) / (int(img.height * 0.4)))
                draw.line([(0, i), (img.width, i)], fill=(0, 0, 0, alpha))
            
            img = Image.alpha_composite(img.convert('RGBA'), gradient)
            
            # Add watermark
            return self.add_watermark(img)
            
        except Exception as e:
            raise Exception(f"Template error: {str(e)}")