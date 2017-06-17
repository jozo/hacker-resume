from flask import Flask, render_template, request, redirect, session
import wakatime
import conf


app = Flask(__name__)
app.secret_key = conf.flask_secret_key


@app.route('/')
def home():
    data = {}
    if session.get('wakatime_code', None):
        wt_session = wakatime.get_session(session['wakatime_code'])
        stats = wt_session.get('users/current/stats/last_year').json()
        data['wakatime_data'] = str(stats.get('data', {}).get('human_readable_total', 'Calculating...'))
    return render_template('home.html', **data)


@app.route('/oauth-wakatime')
def oauth_wakatime():
    session['wakatime_code'] = request.args.get('code')
    return redirect('/')


@app.route('/start-wakatime')
def start_wakatime():
    url = wakatime.get_authorize_url()
    return redirect(url)


if __name__ == '__main__':
    app.run(debug=True)
