from flask import Flask, render_template, request, redirect, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import io
import socket

app = Flask(__name__)
app.secret_key = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50))

@app.before_request
def block_mobile():
    user_agent = request.headers.get('User-Agent', '').lower()
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        return "请使用电脑访问本系统", 403

@app.route('/')
def home():
    if 'username' not in session:
        return redirect('/login')
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect('/')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/attendance', methods=['POST'])
def record_attendance():
    if 'username' not in session:
        return jsonify({"message": "未登录"}), 403
    data = request.get_json()
    existing = Attendance.query.filter_by(username=session['username'], type=data['type']).first()
    if existing:
        return jsonify({"message": f"{data['type']} 已打卡，无需重复"}), 400
    entry = Attendance(username=session['username'], type=data['type'])
    db.session.add(entry)
    db.session.commit()
    return jsonify({"message": f"{data['type']} 打卡成功"})

@app.route('/download')
def download():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '用户名', '时间', '类型'])
    for row in Attendance.query.order_by(Attendance.timestamp.desc()).all():
        writer.writerow([row.id, row.username, row.timestamp, row.type])
    output.seek(0)
    return send_file(io.BytesIO(output.read().encode('utf-8')), mimetype='text/csv',
                     as_attachment=True, download_name='attendance.csv')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=10000)
