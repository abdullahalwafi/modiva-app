from django.shortcuts import render
from django.urls import path

# Dashboard Views

def bidding_view(request):
    context = {'title':'Bidding',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Dashboards","url":""},{"name":"Bidding","url":"dashboards/bidding"}]}
    return render(request,'examples/dashboards/bidding.html',context)

def call_center_view(request):
    context = {'title':'Call-center',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Dashboards","url":""},{"name":"Bidding","url":"dashboards/call-center"}]}
    return render(request,'examples/dashboards/bidding.html',context)

def ecommerce_view(request):
    context = {'title':'Ecommerce',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Dashboards","url":""},{"name":"Bidding","url":"dashboards/ecommerce"}]}
    return render(request,'examples/dashboards/bidding.html',context)

def marketing_view(request):
    context = {'title':'Marketing',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Dashboards","url":""},{"name":"Bidding","url":"dashboards/marketing"}]}
    return render(request,'examples/dashboards/bidding.html',context)

def online_courses_view(request):
    context = {'title':'Online-courses',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Dashboards","url":""},{"name":"Bidding","url":"dashboards/online-courses"}]}
    return render(request,'examples/dashboards/bidding.html',context)

def pos_view(request):
    context = {'title':'POS',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Dashboards","url":""},{"name":"Bidding","url":"dashboards/pos"}]}
    return render(request,'examples/dashboards/bidding.html',context)

def projects_view(request):
    context = {'title':'Projects',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Dashboards","url":""},{"name":"Bidding","url":"dashboards/projects"}]}
    return render(request,'examples/dashboards/bidding.html',context)

urlpatterns = [
    path('pages/bidding', bidding_view),
    path('pages/call-center', call_center_view),
    path('pages/ecommerce', ecommerce_view),
    path('pages/marketing', marketing_view),
    path('pages/online-courses', online_courses_view),
    path('pages/pos', pos_view),
    path('pages/projects', projects_view),
]