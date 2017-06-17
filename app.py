from flask import Flask, render_template, request, redirect, session
import wakatime
import conf


app = Flask(__name__)
app.secret_key = conf.FLASK_SECRET_KEY


def try_get_wakatime_data():
    import pdb ; pdb.set_trace()
    if session.get('wakatime_code', None):
        print('**** SESSION CODE: {}'.format(session['wakatime_code']))
        wt_session = wakatime.get_session(session['wakatime_code'])
        stats = wt_session.get('users/current/stats/last_year').json()
        return str(stats.get('data', {}).get('human_readable_total', 'Calculating...'))
    return None


@app.route('/')
def home():
    data = {'wakatime': try_get_wakatime_data()}
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


if __name__ == '__main__':
    app.run(debug=True)
