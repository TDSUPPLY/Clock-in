import os
from flask import Flask, render_template, request, redirect, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

@app.route('/')
def home():
    if 'username' not in session:
        return redirect('/login')
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        return redirect('/')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        if not User.query.filter_by(username=username).first():
            db.session.add(User(username=username))
            db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/attendance', methods=['POST'])
def record_attendance():
    if 'username' not in session:
        return jsonify({"error": "未登录"}), 401
    username = session['username']
    data = request.get_json()
    att_type = data['type']
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    exists = Attendance.query.filter(
        Attendance.username == username,
        Attendance.type == att_type,
        db.func.strftime('%Y-%m-%d', Attendance.timestamp) == date_str
    ).first()
    if exists:
        return jsonify({"message": f"{att_type} 已打卡"})
    record = Attendance(username=username, type=att_type)
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": f"{att_type} 打卡成功"})

@app.route('/export')
def export():
    records = Attendance.query.order_by(Attendance.timestamp).all()
    if not records:
        return "暂无记录"
    df = pd.DataFrame([{
        '用户名': r.username,
        '打卡类型': r.type,
        '时间': r.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for r in records])
    export_path = '打卡记录.xlsx'
    df.to_excel(export_path, index=False)
    return send_file(export_path, as_attachment=True)

if __name__ == '__main__':
    import os

port = int(os.environ.get('PORT', 5000))

app.run(host='0.0.0.0', port=port)
