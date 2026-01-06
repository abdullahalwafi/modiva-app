from django_components import component
import json

@component.register("heading")
class Heading(component.Component):
    template_name = "heading/heading.html"
    
    def get_context_data(self,title,subtitle,breadcrumb):
        
        if isinstance(breadcrumb, str):
            try:
                breadcrumb = json.loads(breadcrumb)
            except json.JSONDecodeError:
                breadcrumb = []

        return {
            "title": title,
            "subtitle": subtitle,
            "breadcrumb": breadcrumb
        }
