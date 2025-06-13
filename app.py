import os
from flask import Flask, render_template, request, jsonify, redirect, session
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

# ✅ 只在首次运行时自动创建数据库文件
@app.before_first_request
def create_tables():
    if not os.path.exists("app.db"):
        db.create_all()

@app.route('/')
def home():
    if 'username' not in session:
        session['username'] = 'td01'
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/api/attendance', methods=['POST'])
def record_attendance():
    data = request.get_json()
    username = session.get('username', 'unknown')
    entry = Attendance(username=username, type=data['type'])
    db.session.add(entry)
    db.session.commit()
    return jsonify({"message": f"{data['type']} 打卡成功"})

if __name__ == '__main__':
    app.run(debug=True)
