import hashlib
import os
from rauth import OAuth2Service
from conf import WAKATIME_APP_ID, WAKATIME_APP_SECRET


wakatime_service = OAuth2Service(
    client_id=WAKATIME_APP_ID,  # your App ID from https://wakatime.com/apps
    client_secret=WAKATIME_APP_SECRET,  # your App Secret from https://wakatime.com/apps
    name='wakatime',
    authorize_url='https://wakatime.com/oauth/authorize',
    access_token_url='https://wakatime.com/oauth/token',
    base_url='https://wakatime.com/api/v1/')

redirect_uri = 'http://localhost:5000/wakatime-oauth-end'


def get_authorize_url():
    state = hashlib.sha1(os.urandom(40)).hexdigest()
    params = {'scope': 'email,read_stats',
              'response_type': 'code',
              'state': state,
              'redirect_uri': redirect_uri}

    url = wakatime_service.get_authorize_url(**params)
    return url


def get_session(code):
    headers = {'Accept': 'application/x-www-form-urlencoded'}
    session = wakatime_service.get_auth_session(headers=headers,
                                                data={'code': code,
                                                      'grant_type': 'authorization_code',
                                                      'redirect_uri': redirect_uri})
    return session

# print('**** Visit {url} in your browser. ****'.format(url=url))
# print('**** After clicking Authorize, paste code here and press Enter ****')
# code = raw_input('Enter code from url: ')

# Make sure returned state has not changed for security reasons, and exchange
# code for an Access Token.


# user = session.get('users/current').json()
# print(user['data']['email'])
# stats = session.get('users/current/stats').json()
# print(stats.get('data', {}).get('human_readable_total', 'Calculating...'))
