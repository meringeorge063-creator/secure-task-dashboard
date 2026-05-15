from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = "securekey"

bcrypt = Bcrypt(app)

# Create database
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT,
            user TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# Home route
@app.route('/')
def home():
    return redirect('/login')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",
                        (username, password, 'user'))
            conn.commit()
        except:
            return "User already exists"

        conn.close()
        return redirect('/login')

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()

        conn.close()

        if user and bcrypt.check_password_hash(user[2], password):
            session['username'] = username
            session['role'] = user[3]

            if user[3] == 'admin':
                return redirect('/admin')

            return redirect('/dashboard')

        return "Invalid credentials"

    return render_template('login.html')

# Dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    if request.method == 'POST':
        task = request.form['task']

        cur.execute("INSERT INTO tasks(task,user) VALUES(?,?)",
                    (task, session['username']))
        conn.commit()

    cur.execute("SELECT * FROM tasks WHERE user=?",
                (session['username'],))
    tasks = cur.fetchall()

    conn.close()

    return render_template('dashboard.html',
                           tasks=tasks,
                           username=session['username'])

# Delete Task
@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("DELETE FROM tasks WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/dashboard')

# Admin Panel
@app.route('/admin')
def admin():
    if 'role' not in session or session['role'] != 'admin':
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    conn.close()

    return render_template('admin.html', users=users)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)