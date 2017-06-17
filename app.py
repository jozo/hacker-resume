from flask import Flask, render_template, request, redirect, session
from rauth import OAuth2Service
import conf

app = Flask(__name__)
app.secret_key = conf.flask_secret_key


stackexchange_auth = OAuth2Service(
    client_id= conf.STACKEXCHANGE_CLIENT_ID,
    client_secret= conf.STACKEXCHANGE_CLIENT_SECRET,
    name='stackexchange',
    authorize_url= 'https://stackexchange.com/oauth',
    access_token_url='https://stackexchange.com/oauth/access_token',
    base_url='https://stackexchange.com')

redirect_uri = 'http://localhost:5000/oauth-stackexchange'
params = {'client_id': conf.STACKEXCHANGE_CLIENT_ID,
          'response_type': 'code',
          'redirect_uri': redirect_uri}

@app.route('/')
def home():
    if session.get('stackexchange_code', None):
        se_session = stackexchange_auth.get_auth_session(data= {'code': session['stackexchange_code'],
                                                                'redirect_uri': redirect_uri})
        about_me = se_session.get('https://api.stackexchange.com/me/tags',
                       params={'format': 'json', 'site': 'stackoverflow',
                               'access_token': se_session.access_token, 'key': conf.STACKEXCHANGE_KEY}).json()

        print(about_me)
    return render_template('home.html')


@app.route('/oauth-stackexchange')
def oauth_stacexchange():
    session['stackexchange_code'] = request.args.get('code')
    return redirect('/')

@app.route('/start-stackexchange')
def start_wakatime():
    url = stackexchange_auth.get_authorize_url(**params)
    return redirect(url)


if __name__ == '__main__':
    app.run(debug=True)
