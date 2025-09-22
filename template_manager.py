import os

class TemplateManager:
    def __init__(self, template_dir="templates"):
        self.template_dir = template_dir

    def list_templates(self):
        return [f for f in os.listdir(self.template_dir) if f.endswith(".txt")]

    def load_template(self, name):
        path = os.path.join(self.template_dir, name)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def fill_template(self, name, **kwargs):
        template = self.load_template(name)
        if not template:
            return None
        return template.format(**kwargs)
