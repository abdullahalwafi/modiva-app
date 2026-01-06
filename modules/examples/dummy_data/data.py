from django.utils import timezone

# content_files = [
#     f'{filename}'.replace(".html","")
#     for filename in listdir(settings.BASE_DIR / 'templates' / 'examples' / '_guideline' / 'content')
#     if ".html" in filename
# ]


def _create_data(path,num_data=5):
    context = {path:[]}
    for i in range(num_data):
        i += 1
        user_data = {
                "id":i,
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "first_name": f"First{i}",
                "last_name": f"Last{i}",
                "date_joined": timezone.now().isoformat()
        }
        context[path].append(user_data)
    
    return context



