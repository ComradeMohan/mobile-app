import os
from flask import Flask, render_template, request, redirect, url_for, session
from scraper import ARMSClient
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'profile' in session:
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template('index.html', error='Username and password are required')
        
        client = ARMSClient()
        profile = client.fetch_profile(username, password)
        
        if "error" in profile:
            return render_template('index.html', error=profile['error'])
        
        session['profile'] = profile
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

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
