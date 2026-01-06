from django.shortcuts import render
from os import listdir
from django.conf import settings
from ..dummy_data import data

# Create your views here.

def _generate_examples_account():
    return [
        {
            'name':"Account Overview",
            'url':"examples/account/overview",
            'components':[
                'Profil Detail saved form'
            ]
        },
        {
            'name':"Account Settings",
            'url':"examples/account/settings",
            'components':[
                'Profil Detail edited form',
                'Sign-in settings form',
                'Connected Account form',
                'Notification settings list checkbox',
                'Deactivate Account form'
            ]
        },
        {
            'name':"Account Security",
            'url':"examples/account/security",
            'components':[
                'Security Card',
                'Recent Alert Banner',
                'Security Guidelines Banner',
                'Login Session / Licence Usage List'
            ]
        },
        {
            'name':"Account Activity",
            'url':"examples/account/activity",
            'components':[
                'Tracking Activity Logs',
                # 'Recent Alert Banner',
                # 'Security Guidelines Banner',
                # 'Login Session / Licence Usage List'
            ]
        },
        {
            'name':"Account Billing",
            'url':"examples/account/billing",
            'components':[
                'Payment Card',
                'Billing Address',
                'Billing History',
            ]
        },
        {
            'name':"Account Statements",
            'url':"examples/account/statements",
            'components':[
                'Earnings Card',
                'Statements List',
            ]
        },
        {
            'name':"Account Referrals",
            'url':"examples/account/referrals",
            'components':[
                'Referrals Detail Card',
                'Referrals Detail List'
            ]
        },
        {
            'name':"Account Api-Keys",
            'url':"examples/account/api-keys",
            'components':[
                'Api-keys Detail Card',
                'Login Session List',
                'Api-keys List'
            ]
        },
        {
            'name':"Account Logs",
            'url':"examples/account/logs",
            'components':[
                'Log Lists'
            ]
        }
    ]
    
def _generate_examples_widget():
    return [
        {
            'name':"Widget Charts",
            'url':"examples/widgets/charts",
            'components':[
                'Chart bar with floating filter',
                'Chart bar with toolbar filter',
                'Chart line',
                'Chart multiple lines',
                'Chart compound lines',
                'Chart compound lines blurred'
            ]
        },
        {
            'name':"Widgets Feeds",
            'url':"examples/widgets/feeds",
            'components':[
                'Feeds Cards',
            ]
        },
        {
            'name':"widgets Lists",
            'url':"examples/widgets/lists",
            'components':[
                'List Task Overview',
                'List Authors',
                'List Todo',
                'List Trends',
                'List Products',
                'List Activities',
                'List Notification',
                'List Order'
            ]
        },
        {
            'name':"Widgets Mixed",
            'url':"examples/widgets/mixed",
            'components':[
                'Mixed list with card',
                'Mixed card with statistic',
                'Mixed chart with card',
                'Mixed feeds with list',
                'Mixed statistic with feeds'
            ]
        },
        {
            'name':"Widgets Statistics",
            'url':"examples/widgets/statistics",
            'components':[
                'Statistic Chart',
                'Statistic Bar',
                'Statistic Card'
            ]
        },
        {
            'name':"Widgets Statements",
            'url':"examples/widgets/statements",
            'components':[
                'Earnings Card',
                'Statements List',
            ]
        },
        {
            'name':"Widgets Referrals",
            'url':"examples/widgets/referrals",
            'components':[
                'Referrals Detail Card',
                'Referrals Detail List'
            ]
        },
        {
            'name':"Widgets Api-Keys",
            'url':"examples/widgets/api-keys",
            'components':[
                'Api-keys Detail Card',
                'Login Session List',
                'Api-keys List'
            ]
        },
        {
            'name':"Widgets Logs",
            'url':"examples/widgets/logs",
            'components':[
                'Log Lists'
            ]
        }
    ]

def _generate_examples_dashboard():
    return [
        {
            'name':"Dashboard Bidding",
            'url':"examples/pages/bidding",
            'components':[
                'Dashboard Bidding Theme',
            ]
        },
        {
            'name':"Dashboards Call-Center",
            'url':"examples/pages/call-center",
            'components':[
                'Dashboard Call-center',
            ]
        },
        {
            'name':"Dashboards Ecommerce",
            'url':"examples/pages/ecommerce",
            'components':[
                'Dashboard Ecommerce',
            ]
        },
        {
            'name':"Dashboards Marketing",
            'url':"examples/pages/marketing",
            'components':[
                'Dashboard Marketing',
            ]
        },
        {
            'name':"Dashboards Online-course",
            'url':"examples/pages/online-courses",
            'components':[
                'Dashboard Online-course',
            ]
        },
        {
            'name':"Dashboards POS",
            'url':"examples/pages/pos",
            'components':[
                'Dashboard POS',
            ]
        },
        {
            'name':"Dashboards Projects",
            'url':"examples/pages/projects",
            'components':[
                'Dashboard Projects',
            ]
        },
    ]

def _get_context_examples():
    account_examples = _generate_examples_account()
    widget_examples = _generate_examples_widget()
    dashboards_examples = _generate_examples_dashboard()
    return [
        *account_examples,
        *widget_examples,
        *dashboards_examples,
    ]

def index_examples(request):
    examples_pages = _get_context_examples() 
    context = {
        'data':[["name","components"],examples_pages]
    }
    return render(request,'examples/index.html',context)

def _get_side_lists():
    return [
        {
            'name':'Getting started',
            'items':[
                ('Desain Sistem','desain-sistem'),
                ('Menggunakan Komponen','menggunakan-komponen'),
                ('Membuat Komponen','membuat-komponen'),
            ],
        },
        {
            'name':'Components',
            'items':[
                ('tables','tables'),
                ('forms','forms'),
                ('heading','heading'),
                ('card','card'),
            ]
        },
        
    ]

context = {'side_lists':_get_side_lists()}
content_files = [
        f'{filename}'.replace(".html","")
        for filename in listdir(settings.BASE_DIR / 'templates' / 'examples' / '_guideline' / 'content')
        if ".html" in filename
    ]

def documentation(request,context=context):
    return render(request,'examples/_guideline/index.html',context)

def index_documentation(request,path,context=context):
    file = 'index'
    # context = {'side_lists':_get_side_lists()}
    if path in content_files:
        file = 'content/' + path
    if 'tables' == path:
        context.update(data._create_data(path,50))
        
    return render(request,f'examples/_guideline/{file}.html',context)
