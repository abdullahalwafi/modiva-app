from django.shortcuts import render
# Create your views here.
from django.http import HttpResponse

def dashboard(request):
    #return HttpResponse("Welcome to Backend - Index page")
    template_name = 'backend/dashboard.html'
    title = 'Ini Halaman Dashboard'
    data = {'page_title': title, 'message': 'Hello Dashbaord'}
    
    return render(request, template_name,context=data)