from flask import Flask, render_template, request, redirect, session, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.secret_key = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50))
    date = db.Column(db.String(20))

@app.route('/')
def home():
    if 'username' not in session:
        return redirect('/login')
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
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
        else:
            return "用户已存在，请返回重新输入"
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/attendance', methods=['POST'])
def attendance():
    if 'username' not in session:
        return jsonify({"error": "未登录"}), 401
    data = request.get_json()
    type = data['type']
    today = datetime.now().strftime('%Y-%m-%d')
    exists = Attendance.query.filter_by(username=session['username'], type=type, date=today).first()
    if exists:
        return jsonify({"message": f"{type} 已打卡"})
    record = Attendance(username=session['username'], type=type, date=today)
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": f"{type} 打卡成功"})

@app.route('/export')
def export():
    if 'username' not in session:
        return redirect('/login')

    records = Attendance.query.order_by(Attendance.username, Attendance.date, Attendance.timestamp).all()

    # 汇总结构：{(username, date): {type: time}}
    from collections import defaultdict
    grouped = defaultdict(dict)

    for r in records:
        key = (r.username, r.date)
        grouped[key][r.type] = r.timestamp.strftime('%H:%M:%S')

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['日期', '用户名', '上班时间', '下班时间', '上班时长', '午餐开始', '午餐结束', '午餐时长', '加班开始', '加班结束', '加班时长'])

    def calc_hours(start, end):
        from datetime import datetime
        fmt = '%H:%M:%S'
        try:
            delta = datetime.strptime(end, fmt) - datetime.strptime(start, fmt)
            return round(delta.total_seconds() / 3600, 2)
        except:
            return ''

    for (username, date), types in grouped.items():
        上班 = types.get('上班打卡', '')
        下班 = types.get('下班打卡', '')
        午餐开始 = types.get('午餐开始', '')
        午餐结束 = types.get('午餐结束', '')
        加班开始 = types.get('加班开始', '')
        加班结束 = types.get('加班结束', '')

        writer.writerow([
            date, username, 上班, 下班, calc_hours(上班, 下班) if 上班 and 下班 else '',
            午餐开始, 午餐结束, calc_hours(午餐开始, 午餐结束) if 午餐开始 and 午餐结束 else '',
            加班开始, 加班结束, calc_hours(加班开始, 加班结束) if 加班开始 and 加班结束 else ''
        ])

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='打卡记录汇总.csv')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=10000)
