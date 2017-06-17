from flask import Flask, render_template, request, redirect, session
from rauth import OAuth2Service
import wakatime
import conf
import mock


app = Flask(__name__)
app.secret_key = conf.FLASK_SECRET_KEY


stackexchange_auth = OAuth2Service(
    client_id=conf.STACKEXCHANGE_CLIENT_ID,
    client_secret=conf.STACKEXCHANGE_CLIENT_SECRET,
    name='stackexchange',
    authorize_url='https://stackexchange.com/oauth',
    access_token_url='https://stackexchange.com/oauth/access_token',
    base_url='https://stackexchange.com')

github = OAuth2Service(
    name='github',
    client_id= conf.GITHUB_CLIENT_ID,
    client_secret= conf.GITHUB_CLIENT_SECRET,
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize')

redirect_uri = 'http://localhost:5000/oauth-stackexchange'
params = {'client_id': conf.STACKEXCHANGE_CLIENT_ID,
          'response_type': 'code',
          'redirect_uri': redirect_uri}


def try_get_wakatime_data():
    if conf.WAKATIME_MOCK:
        return mock.WAKATIME_STATS
    try:
        if session.get('wakatime_code', None):
            print('**** SESSION CODE: {}'.format(session['wakatime_code']))
            wt_session = wakatime.get_session(session['wakatime_code'])
            stats = wt_session.get('users/current/stats/last_year').json()
            return str(stats.get('data', {}).get('human_readable_total', 'Calculating...'))
    except Exception:
        pass
    return None


def parse_github():
    if session.get('github_code', None):
        github_session = github.get_auth_session(data={'code': session['github_code']})
        about_me = github_session.get('https://api.github.com/user',
                                      params={'access_token': github_session.access_token}).json()
        print("Github:", about_me)
    return None

@app.route('/')
def home():
    # if session.get('stackexchange_code', None):
    #     se_session = stackexchange_auth.get_auth_session(data={'code': session['stackexchange_code'],
    #                                                            'redirect_uri': redirect_uri})
    #     about_me = se_session.get('https://api.stackexchange.com/me/tags',
    #                               params={'format': 'json', 'site': 'stackoverflow',
    #                                       'access_token': se_session.access_token,
    #                                       'key': conf.STACKEXCHANGE_KEY}).json()
    #
    #     print(about_me)
    data = {'wakatime': try_get_wakatime_data()}
    parse_github()
    return render_template('home.html', **data)


@app.route('/wakatime-oauth-end')
def wakatime_oauth_end():
    print('**** CODE: {}'.format(request.args.get('code')))
    session['wakatime_code'] = request.args.get('code')
    return redirect('/')


@app.route('/wakatime-oauth-start')
def wakatime_oauth_start():
    url = wakatime.get_authorize_url()
    return redirect(url)


@app.route('/oauth-stackexchange')
def oauth_stacexchange():
    session['stackexchange_code'] = request.args.get('code')
    return redirect('/')

@app.route('/oauth-github')
def oauth_github():
    session['github_code'] = request.args.get('code')
    return redirect('/')

@app.route('/start-stackexchange')
def start_stackexchange():
    url = stackexchange_auth.get_authorize_url(**params)
    return redirect(url)

@app.route('/start-github')
def start_github():
    url = github.get_authorize_url()
    return redirect(url)


if __name__ == '__main__':
    app.run(debug=True)
