# all the imports
import sqlite3
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])
    
def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()    

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
        
@app.route('/')
def show_entries():
    if session.get('logged_in'):
        cur = g.db.execute('select text from entries where username="{0}" order by id desc'.format(session.get('username')))
        entries = [dict(text=entry[0]) for entry in cur.fetchall()]
        return render_template('show_entries.html', entries=entries, username=session.get('username'))
    else:
        return render_template('show_entries_public.html')
    
@app.route('/api/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (username, text) values (?, ?)', 
                    [session.get('username'), request.form['text']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect('/')
    
    
@app.route('/api/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        cur = g.db.execute('SELECT EXISTS(SELECT 1 FROM users WHERE username="{0}" LIMIT 1)'.format(request.form['username']))
        if cur.fetchall()[0][0] == 1:
            cur = g.db.execute('select text from entries where username="{0}" order by id desc'.format(request.form['username']))
            entries = [dict(text=entry[0]) for entry in cur.fetchall()]
            session['entries'] = entries
            session['logged_in'] = True
            session['username'] = request.form['username']
            flash('Log successfully')
            return redirect(url_for('show_entries'))
        else:
            g.db.execute('insert into users (username) values (?)', [request.form['username']])
            g.db.commit()
            session['logged_in'] = True
            session['username'] = request.form['username']
            flash('new {0} user created!'.format(session['username']))
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))
    



if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080)