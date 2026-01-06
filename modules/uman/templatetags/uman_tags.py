from django import template
from django.template.loader import get_template
from modules.uman.models import Menu


register = template.Library()

@register.simple_tag
def menu_full_path(menu):
    if menu.parent is None or menu.parent == 0:
         return f'{menu.aplikasi} / {menu.name}'
    else:
         menu_label = [menu.name]
         m = menu
         for i in range(6):
              try:
                   menu_label.insert(0,m.parent.name)
                   m = m.parent
              except:
                   menu_label.insert(0,menu.aplikasi.name)
                   break
         return " / ".join(menu_label)


@register.simple_tag
def menu_parent_path(menu):
    if menu.parent is None or menu.parent == 0:
         return f'{menu.aplikasi} /'
    else:
         menu_label = []
         m = menu
         for i in range(6):
              try:
                   menu_label.insert(0,m.parent.name)
                   m = m.parent
              except:
                   menu_label.insert(0,menu.aplikasi.name)
                   break
         return " / ".join(menu_label)

@register.simple_tag
def only_parent_path(menu):
    if menu.parent is None or menu.parent == 0:
         return f'/'
    else:
         menu_label = []
         m = menu
         for i in range(6):
              try:
                   menu_label.insert(0,m.parent.name)
                   m = m.parent
              except:
                   #menu_label.insert(0,menu.aplikasi.name)
                   break
         return " / ".join(menu_label)
