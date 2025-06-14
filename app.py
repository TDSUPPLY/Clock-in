
from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if 'username' not in session:
        return redirect('/login')
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect('/')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/attendance', methods=['POST'])
def attendance():
    data = request.get_json()
    username = session.get('username', 'unknown')
    type = data['type']
    existing = Attendance.query.filter_by(username=username, type=type, timestamp=datetime.today().date()).first()
    if existing:
        return jsonify({"message": f"{type} 已打卡"}), 200
    entry = Attendance(username=username, type=type)
    db.session.add(entry)
    db.session.commit()
    return jsonify({"message": f"{type} 打卡成功"}), 200

if __name__ == '__main__':
    app.run(debug=True)
