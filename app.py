from flask import Flask, render_template, request, redirect, session
from rauth import OAuth2Service
import wakatime
import conf
import mock
import requests
from datetime import datetime
from collections import OrderedDict


app = Flask(__name__)
app.secret_key = conf.FLASK_SECRET_KEY


stackexchange_auth = OAuth2Service(
    client_id=conf.STACKEXCHANGE_CLIENT_ID,
    client_secret=conf.STACKEXCHANGE_CLIENT_SECRET,
    name='stackexchange',
    authorize_url='https://stackexchange.com/oauth',
    access_token_url='https://stackexchange.com/oauth/access_token',
    base_url='https://stackexchange.com')

redirect_uri = 'http://localhost:5000/oauth-stackexchange'
params = {'client_id': conf.STACKEXCHANGE_CLIENT_ID,
          'response_type': 'code',
          'redirect_uri': redirect_uri}

github = OAuth2Service(
    name='github',
    client_id=conf.GITHUB_CLIENT_ID,
    client_secret=conf.GITHUB_CLIENT_SECRET,
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize')


def try_get_wakatime_data():
    if conf.WAKATIME_MOCK:
        return mock.WAKATIME_STATS
    try:
        if session.get('wakatime_code', None):
            print('**** SESSION CODE: {}'.format(session['wakatime_code']))
            wt_session = wakatime.get_session(session['wakatime_code'])
            stats = wt_session.get('users/current/stats/last_year').json()
            session.pop('wakatime_code')
            return stats
    except Exception:
        pass
    return None


def parse_stackexchange():
    if conf.STACKEXCHANGE_MOCK:
        return {'about': mock.STACKEXCHANGE_ABOUT_ME['items'],
                'tags': mock.STACKEXCHANGE_TOP_TAGS['items'],
                'reputation': mock.STACKEXCHANGE_REPUTATION['items']}
    if session.get('stackexchange_code', None):
        se_session = stackexchange_auth.get_auth_session(data={'code': session['stackexchange_code'],
                                                               'redirect_uri': redirect_uri,
                                                               'expires': 10000})
        se_params = {'format': 'json', 'site': 'stackoverflow',
                  'access_token': se_session.access_token,
                  'key': conf.STACKEXCHANGE_KEY}
        tags = se_session.get('https://api.stackexchange.com/me/top-tags', params=se_params).json()
        about_me = se_session.get('https://api.stackexchange.com/me', params=se_params).json()
        reputation = se_session.get('https://api.stackexchange.com/me/reputation', params=se_params).json()
        return {'about': about_me['items'],
                'tags': tags['items'],
                'reputation_change': reputation['items']}
    return None


def join_wakatime_github_langs(github_data, wakatime_data):
    github_langs = [(l.lower().replace(' ','-'),c) for l,c in github_data['language_sumary'].items()]
    github_od = OrderedDict(sorted(github_langs, key=lambda t: t[1], reverse=True))

    wakatime_langs = [(l['name'].lower().replace(' ','-'), l['text']) for l in wakatime_data['data']['languages']]
    wakatime_od = OrderedDict(sorted(wakatime_langs, key=lambda t: t[1], reverse=True))

    final_set = []
    for (name, count) in wakatime_od.items():
        final_set.append({'name': name, 'github_count': github_od.get(name, 0), 'wakatime_hours': count})

    return final_set


def parse_github():
    if conf.GITHUB_MOCK:
        return mock.GITHUB_STATS
    if session.get('github_access_token', None):
        about_me = requests.get('https://api.github.com/user',
                                      params={'access_token': session['github_access_token']}).json()
        user = about_me['login']
        repos = requests.get('https://api.github.com/users/%s/repos' % user,
                                      params={'access_token': session['github_access_token']}).json()
        language_summary = {}
        repo_summary = {}

        for repo in repos:
            repo_name = repo['name']
            repo_langs = requests.get('https://api.github.com/repos/%s/%s/languages' % (user, repo_name),
                                            params={'access_token': session['github_access_token']}).json()

            repo_commits = requests.get('https://api.github.com/repos/%s/%s/commits' % (user, repo_name),
                                              params={'author': user, 'access_token': session['github_access_token']}).json()

            repo_summary[repo_name] = {'number_commits': len(repo_commits), 'languages': repo_langs}
            language_summary = {k: language_summary.get(k, 0) + repo_langs.get(k, 0) for k in
                               set(language_summary) | set(repo_langs)}

        return {'language_summary': language_summary, 'repo_summary': repo_summary}
    return None


def repos_for_langs(data, langs):
    repo_langs_sum = {}
    for l in langs:
        repo_langs_sum[l] = []
    for d in data['repo_sumary']:
        repo_langs = set(map(lambda a: a.lower().replace(' ','-') ,data['repo_sumary'][d]['languages'].keys()))
        intersect = repo_langs.intersection(langs)
        if intersect:
            for lang in intersect:
                repo_langs_sum[lang].append(d)

    return repo_langs_sum


@app.route('/')
def home():
    data = {
        'connected_wakatime': session.get('wakatime_code', False),
        'connected_stackexchange': session.get('stackexchange_code', False),
        'connected_github': session.get('github_access_token', False),
    }
    return render_template('home.html', **data)


@app.route('/resume')
def resume():
    data = {'wakatime': try_get_wakatime_data(),
            'stackoverflow': parse_stackexchange(),
            'github': parse_github()}
    sorted_langs = join_wakatime_github_langs(data['github'], data['wakatime'])
    repos_per_lang = repos_for_langs(data['github'], set(map(lambda a: a['name'], sorted_langs[:5])))
    data['github_sorted_langs'] = sorted_langs
    data['github_repos_per_lang'] = repos_per_lang
    print(data)
    return render_template('resume.html', **data)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/wakatime-oauth-start')
def wakatime_oauth_start():
    url = wakatime.get_authorize_url()
    return redirect(url)


@app.route('/wakatime-oauth-end')
def wakatime_oauth_end():
    print('**** CODE: {}'.format(request.args.get('code')))
    session['wakatime_code'] = request.args.get('code')
    return redirect('/')


@app.route('/start-stackexchange')
def start_stackexchange():
    url = stackexchange_auth.get_authorize_url(**params)
    return redirect(url)


@app.route('/oauth-stackexchange')
def oauth_stacexchange():
    session['stackexchange_code'] = request.args.get('code')
    return redirect('/')


@app.route('/start-github')
def start_github():
    url = github.get_authorize_url()
    return redirect(url)


@app.route('/oauth-github')
def oauth_github():
    github_session = github.get_auth_session(data={'code': request.args.get('code')})
    session['github_access_token'] = github_session.access_token
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
