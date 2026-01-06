from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse


# Create your views here.
def index(request):
    return HttpResponse('<h1>Mytask Works</h1>')
    
