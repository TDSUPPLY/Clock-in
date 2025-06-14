
import os
from flask import Flask, render_template, request, jsonify, redirect, session, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50))

@app.route('/')
def home():
    if 'username' not in session:
        return redirect('/login')
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        session['username'] = username
        return redirect('/')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        session['username'] = username
        return redirect('/')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/attendance', methods=['POST'])
def record_attendance():
    data = request.get_json()
    username = session.get('username', 'unknown')
    existing = Attendance.query.filter_by(username=username, type=data['type']).first()
    if existing:
        return jsonify({"message": f"{data['type']} 已打卡"})
    entry = Attendance(username=username, type=data['type'])
    db.session.add(entry)
    db.session.commit()
    return jsonify({"message": f"{data['type']} 打卡成功"})

@app.route('/export')
def export():
    records = Attendance.query.all()
    output = "ID,Username,Time,Type\n"
    for r in records:
        output += f"{r.id},{r.username},{r.timestamp},{r.type}\n"
    with open("attendance.csv", "w", encoding="utf-8") as f:
        f.write(output)
    return send_file("attendance.csv", as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
