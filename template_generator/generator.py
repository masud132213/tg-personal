from PIL import Image, ImageDraw, ImageFont
from .templates import TEMPLATES
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class TemplateGenerator:
    def __init__(self):
        self.font_path = os.path.join('assets', 'font.ttf')
        self.logo_path = os.path.join('assets', 'logo.png')
        self.current_state = {}
        
    def start_template(self, user_id):
        """Initialize template generation process"""
        self.current_state[user_id] = {
            'step': 'title',
            'title': None,
            'genres': None,
            'quality': None,
            'link': None
        }
        return "পোস্টারের ছবি পাঠান 🖼️"
        
    def process_step(self, user_id, text):
        """Process each step of template generation"""
        print(f"Processing step for user {user_id}")
        print(f"Text received: {text}")
        
        if user_id not in self.current_state:
            print("User not in current_state")
            return "দয়া করে আগে /t কমান্ড দিয়ে শুরু করুন।"
            
        state = self.current_state[user_id]
        print(f"Current state: {state}")
        
        if state['step'] == 'title':
            state['title'] = text
            state['step'] = 'genres'
            print("Moving to genres step")
            return "জনরা লিখুন (উদাহরণ: Action, Adventure) 🎭"
            
        elif state['step'] == 'genres':
            state['genres'] = text
            state['step'] = 'quality'
            print("Moving to quality step")
            return "কোয়ালিটি লিখুন (উদাহরণ: 4K HDR, 1080p) ✨"
            
        elif state['step'] == 'quality':
            state['quality'] = text
            state['step'] = 'link'
            print("Moving to link step")
            return "ডাউনলোড লিংক দিন 🔗"
            
        elif state['step'] == 'link':
            state['link'] = text
            state['step'] = 'template'
            print("Moving to template selection")
            
            # Create template selection keyboard
            keyboard = []
            for i in range(1, 4):
                keyboard.append([
                    InlineKeyboardButton(
                        f"টেমপ্লেট {i}", 
                        callback_data=f"template_{i}_{user_id}"
                    )
                ])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            return ("টেমপ্লেট সিলেক্ট করুন:", reply_markup)
            
        return "কিছু ভুল হয়েছে! /t দিয়ে আবার শুরু করুন।"

    def generate_template(self, template_num, user_id, image_path):
        """Generate the final template"""
        if user_id not in self.current_state:
            return None
            
        state = self.current_state[user_id]
        template = TEMPLATES[f"template{template_num}"]
        
        try:
            # Open and process image
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Add gradient overlay
            gradient = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(gradient)
            
            # Create vertical gradient
            for i in range(img.height):
                alpha = int(255 * (0.3 if i < img.height/2 else (i - img.height/2)/(img.height/2)))
                draw.line([(0, i), (img.width, i)], fill=(0, 0, 0, alpha))
            
            img = Image.alpha_composite(img.convert('RGBA'), gradient)
            
            # Add text
            draw = ImageDraw.Draw(img)
            
            # Calculate font sizes
            title_font_size = int(img.width * 0.08)
            info_font_size = int(img.width * 0.04)
            desc_font_size = int(img.width * 0.035)
            
            # Load fonts
            title_font = ImageFont.truetype(self.font_path, title_font_size)
            info_font = ImageFont.truetype(self.font_path, info_font_size)
            desc_font = ImageFont.truetype(self.font_path, desc_font_size)
            
            # Add title
            title_text = template['title_text'].format(title=state['title'])
            title_width = draw.textlength(title_text, font=title_font)
            title_position = (int((img.width - title_width) / 2), int(img.height * 0.6))
            
            # Add shadow/glow to title
            for offset in [(x, y) for x in range(-2, 3) for y in range(-2, 3)]:
                draw.text(
                    (title_position[0] + offset[0], title_position[1] + offset[1]),
                    title_text,
                    font=title_font,
                    fill=(0, 0, 0, 100)
                )
            draw.text(title_position, title_text, font=title_font, fill=template['colors']['title'])
            
            # Add genres
            genres_text = template['genres_text'].format(genres=state['genres'])
            genres_width = draw.textlength(genres_text, font=info_font)
            genres_position = (
                int((img.width - genres_width) / 2),
                title_position[1] + title_font_size + 20
            )
            draw.text(genres_position, genres_text, font=info_font, fill=template['colors']['genres'])
            
            # Add quality
            quality_text = template['quality_text'].format(quality=state['quality'])
            quality_width = draw.textlength(quality_text, font=info_font)
            quality_position = (
                int((img.width - quality_width) / 2),
                genres_position[1] + info_font_size + 10
            )
            draw.text(quality_position, quality_text, font=info_font, fill=template['colors']['quality'])
            
            # Add description
            for i, desc in enumerate(template['description']):
                desc_width = draw.textlength(desc, font=desc_font)
                desc_position = (
                    int((img.width - desc_width) / 2),
                    quality_position[1] + info_font_size + 20 + (i * (desc_font_size + 5))
                )
                draw.text(desc_position, desc, font=desc_font, fill=template['colors']['description'])
            
            # Add download button
            button_text = f"{template['icons']['download']} Download Now"
            
            return img.convert('RGB'), button_text, state['link']
            
        except Exception as e:
            print(f"Error generating template: {e}")
            return None 