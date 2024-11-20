import json

class TemplateManager:
    def __init__(self):
        self.templates = self.load_templates()
    
    def load_templates(self):
        with open('templates.json', 'r') as f:
            return json.load(f)
    
    def apply_template(self, image, template_name):
        if template_name in self.templates:
            template = self.templates[template_name]
            # Apply template settings
            # (position, size, effects etc.)
            return processed_image
        return image 