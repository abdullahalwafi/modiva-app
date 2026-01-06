from django_components import component

@component.register("text")
class text(component.Component):
    template_name = "form_input/text.html"

@component.register("text_row")
class textrow(component.Component):
    template_name = "form_input/text_row.html"
    
@component.register("textarea")
class textarea(component.Component):
    template_name = "form_input/textarea.html"

@component.register("textarea_row")
class textarearow(component.Component):
    template_name = "form_input/textarea_row.html"

@component.register("dropdown")
class dropdown(component.Component):
    template_name = "form_input/dropdown.html"

@component.register("dropdownlist")
class dropdownlist(component.Component):
    template_name = "form_input/dropdownlist.html"

@component.register("checkbox")
class checkbox(component.Component):
    template_name = "form_input/checkbox.html"
    
@component.register("radio")
class radio(component.Component):
    template_name = "form_input/radio.html"
    
@component.register("toggle")
class toggle(component.Component):
    template_name = "form_input/toggle.html"

@component.register("date_picker")
class date_picker(component.Component):
    template_name = "form_input/date_picker.html"
    