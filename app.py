from flask import Flask, render_template, request, redirect, url_for, session
from scraper import ARMSClient
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # secure random key for sessions

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'profile' in session:
        return redirect(url_for('profile'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        client = ARMSClient()
        profile = client.fetch_profile(username, password)

        if "error" in profile:
            return render_template('index.html', error=profile['error'])

        session['profile'] = profile  # store in cookie session
        return redirect(url_for('profile'))

    return render_template('index.html')


@app.route('/profile')
def profile():
    if 'profile' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html', profile=session['profile'])


@app.route('/logout')
def logout():
    session.pop('profile', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
