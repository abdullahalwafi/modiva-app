import requests
import json
from .config import *

"""
MYTASK_URL_AUTH="https://sso.kemenkeu.go.id/connect/token"
MYTASK_URL_SERVICE="https://service.kemenkeu.go.id/otomasi.agenda/api/SystemTask/Create"
MYTASK_CLIENT_ID="sikd.task"
MYTASK_CLIENT_SECRET="923d24e9119c4c8e8891187078b2984a"
MYTASk_SCOPE="hris2 systemtask"
MYTASK_GRANT_TYPE="client_credentials"
"""


def get_token():
    data = { "client_id": MYTASK_CLIENT_ID , "client_secret": MYTASK_CLIENT_SECRET, "grant_type": MYTASK_GRANT_TYPE,"scope": MYTASK_SCOPE }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    url = MYTASK_URL_AUTH
    try:
        response = requests.post( url, headers=headers, data=data)
        if response.status_code == 200:
            return {
                'success': True,
                'access_token': dict(response.json())['access_token']
            }
        else:
            return {
                'success': False,
                'error': '',
                'access_token': None
            }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': e,
            'access_token': None
        }



def create_mytask(userID, startTime, endTime, duration, produkID):
    
    url = MYTASK_URL_SERVICE
    data = json.dumps({
        "userID": userID,
        "message": [
            {
                "startTime": startTime,
                "endTime": endTime,
                "duration": duration,
                "tahapanID": int(produkID)
            }
        ]
    })

    token_request = get_token()
    access_token = token_request['access_token']
    #print('access token -> ',access_token)
    if not token_request["success"]:
         return token_request

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            return {
                'success': True,
                'data': response.json()
            }
        else:
            return {
                'success': False,
                'data': None,
                'error': response.json()
            } 
    except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'data': None,
                'error': e
            } 

if __name__ == '__main__':
    print(get_token())
