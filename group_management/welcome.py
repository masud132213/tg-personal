import random

class WelcomeManager:
    def __init__(self):
        self.templates = [
            """
            🌟 স্বাগতম {name}!
            
            CinemazBD - বাংলাদেশের সেরা মুভি/সিরিজ সাইট
            ✨ HD কোয়ালিটি
            🚀 সুপার ফাস্ট ডাউনলোড
            💫 নতুন রিলিজ সবার আগে
            """,
            """
            🎬 হ্যালো {name}!
            
            CinemazBD তে পাবেন:
            🎯 সব ধরনের মুভি/সিরিজ
            🎭 ডাবিং/সাবটাইটেল সহ
            ⚡️ ডাইরেক্ট ডাউনলোড
            """,
            """
            🎉 স্বাগতম {name} CinemazBD পরিবারে!
            
            আমাদের বৈশিষ্ট্য:
            🔥 4K/HDR কোয়ালিটি
            🎯 ডুয়াল অডিও
            ⚡️ গুগল ড্রাইভ/ডাইরেক্ট ডাউনলোড
            🌟 রিকোয়েস্ট সিস্টেম
            """,
            """
            ✨ স্বাগতম {name}!
            
            CinemazBD - একটি প্রিমিয়াম মুভি/সিরিজ সাইট
            
            🎯 আমাদের সুবিধাসমূহ:
            • নতুন মুভি সবার আগে
            • সকল ওটিটি সিরিজ
            • ডাবিং/সাবটাইটেল সহ
            • অ্যাড ফ্রি ডাউনলোড
            """,
            """
            🌟 Welcome {name}!
            
            CinemazBD - Your Ultimate Entertainment Hub
            
            What We Offer:
            🎬 Latest Movies & Series
            🎯 Multiple Audio Tracks
            💫 High Quality Content
            ⚡️ Fast Download Speed
            """,
            """
            🎬 স্বাগতম {name}!
            
            CinemazBD এ আপনি পাবেন:
            
            • নেটফ্লিক্স/অ্যামাজন/হটস্টার সিরিজ
            • হলিউড/বলিউড/কোরিয়ান মুভি
            • ওয়েব সিরিজ/এনিমে
            • ডাবিং/সাবটাইটেল সহ
            
            আপনার পছন্দের সব কনটেন্ট এক জায়গায়!
            """,
            """
            ⭐️ হ্যালো {name}!
            
            CinemazBD - প্রিমিয়াম এন্টারটেইনমেন্ট হাব
            
            বৈশিষ্ট্যসমূহ:
            🎯 4K/HDR কোয়ালিটি
            🎬 মাল্টি অডিও ট্র্যাক
            💫 সাবটাইটেল সাপোর্ট
            ⚡️ ফাস্ট ডাউনলোড
            🌟 24/7 সাপোর্ট
            """
        ]
    
    def get_random_template(self, user_name, website_link):
        template = random.choice(self.templates)
        message = template.format(name=user_name)
        
        # Add website button if link exists
        buttons = []
        if website_link:
            buttons.append([{
                'text': '🌐 আমাদের ওয়েবসাইট',
                'url': website_link
            }])
            
        return message, buttons 