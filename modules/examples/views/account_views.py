from django.shortcuts import render
from django.urls import path

# Account Views

def account_overview_view(request):
    context = {'title':'Overview',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Account","url":""}]}
    return render(request,'examples/account/overview.html',context)

def account_api_keys_view(request):
    context = {'title':'Api-keys',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Account","url":""}]}
    return render(request,'examples/account/api-keys.html',context)

def account_billing_view(request):
    context = {'title':'Billing',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Account","url":""}]}
    return render(request,'examples/account/billing.html',context)

def account_logs_view(request):
    context = {'title':'Logs',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Account","url":""}]}
    return render(request,'examples/account/logs.html',context)

def account_activity_view(request):
    context = {'title':'Activity',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Account","url":""}]}
    return render(request,'examples/account/activity.html',context)

def account_referrals_view(request):
    context = {'title':'referrals',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Account","url":""}]}
    return render(request,'examples/account/referrals.html',context)

def account_security_view(request):
    context = {'title':'security',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Account","url":""}]}
    return render(request,'examples/account/security.html',context)

def account_settings_view(request):
    context = {'title':'settings',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Account","url":""}]}
    return render(request,'examples/account/settings.html',context)

def account_statements_view(request):
    context = {'title':'statements',
               'subtitle':'XHR234',
               'breadcrumb':[{"name":"Home","url":""},{"name":"Account","url":""}]}
    return render(request,'examples/account/statements.html',context)

urlpatterns = [
    path('account/overview', account_overview_view),
    path('account/api-keys', account_api_keys_view),
    path('account/settings', account_settings_view),
    path('account/billing', account_billing_view),
    path('account/logs', account_logs_view),
    path('account/activity', account_activity_view),
    path('account/referrals', account_referrals_view),
    path('account/security', account_security_view),
    path('account/statements', account_statements_view),
]
