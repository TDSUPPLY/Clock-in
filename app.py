from flask import Flask, render_template, request, redirect, session, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import csv
import io
from collections import defaultdict

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

def malaysia_now():
    return datetime.utcnow() + timedelta(hours=8)

@app.route('/api/attendance', methods=['POST'])
def attendance():
    if 'username' not in session:
        return jsonify({"error": "未登录"}), 401
    data = request.get_json()
    type = data['type']
    now = malaysia_now()
    today = now.strftime('%Y-%m-%d')
    
    if type in ['上班打卡', '午餐开始', '加班开始']:
        exists = Attendance.query.filter_by(username=session['username'], type=type, date=today).first()
        if exists:
            return jsonify({"message": f"{type} 已打卡（首次记录为准）"})
        record = Attendance(username=session['username'], type=type, date=today, timestamp=now)
        db.session.add(record)
        db.session.commit()
        return jsonify({"message": f"{type} 打卡成功"})

    elif type in ['下班打卡', '午餐结束', '加班结束']:
        # 删除旧的打卡记录，保留最新时间
        Attendance.query.filter_by(username=session['username'], type=type, date=today).delete()
        record = Attendance(username=session['username'], type=type, date=today, timestamp=now)
        db.session.add(record)
        db.session.commit()

        if type == '午餐结束':
            lunch_start = Attendance.query.filter_by(username=session['username'], type='午餐开始', date=today).first()
            if lunch_start:
                duration = (now - lunch_start.timestamp).total_seconds() / 60
                if duration > 40:
                    return jsonify({"message": "午餐超时（超过40分钟）"})
                elif duration > 30:
                    return jsonify({"message": "午餐已超过30分钟，请尽快返回岗位"})
        return jsonify({"message": f"{type} 打卡成功（记录以最后一次为准）"})

    return jsonify({"error": "无效的打卡类型"}), 400

@app.route('/export')
def export():
    if 'username' not in session:
        return redirect('/login')

    records = Attendance.query.order_by(Attendance.username, Attendance.date, Attendance.timestamp).all()
    grouped = defaultdict(dict)
    for r in records:
        key = (r.username, r.date)
        grouped[key][r.type] = r.timestamp.strftime('%H:%M:%S')

    def calc_hours(start, end):
        fmt = '%H:%M:%S'
        try:
            delta = datetime.strptime(end, fmt) - datetime.strptime(start, fmt)
            return round(delta.total_seconds() / 3600, 2)
        except:
            return ''

    def calc_minutes(start, end):
        fmt = '%H:%M:%S'
        try:
            delta = datetime.strptime(end, fmt) - datetime.strptime(start, fmt)
            return round(delta.total_seconds() / 60)
        except:
            return 0

    def get_expect_time(date, is_start):
        day = datetime.strptime(date, '%Y-%m-%d').weekday()
        if is_start:
            return '09:00:00'
        else:
            return '16:00:00' if day == 5 else '17:30:00'

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['日期', '用户名', '上班时间', '下班时间', '午餐开始', '午餐结束',
                     '总工作时长(h)', '午餐时长(h)', '加班时长(h)',
                     '迟到时间(min)', '早退时间(min)', '异常次数', '午餐超时(min)'])

    for (username, date), types in grouped.items():
        上班 = types.get('上班打卡', '')
        下班 = types.get('下班打卡', '')
        午餐开始 = types.get('午餐开始', '')
        午餐结束 = types.get('午餐结束', '')
        加班开始 = types.get('加班开始', '')
        加班结束 = types.get('加班结束', '')

        work_hours = calc_hours(上班, 下班)
        lunch_hours = calc_hours(午餐开始, 午餐结束)
        overtime_hours = calc_hours(加班开始, 加班结束)
        total_work_hours = round((work_hours or 0) - (lunch_hours or 0.5), 2) if work_hours else ''
        late_minutes = calc_minutes(get_expect_time(date, True), 上班) if 上班 else 0
        early_minutes = calc_minutes(下班, get_expect_time(date, False)) if 下班 else 0
        lunch_minutes = calc_minutes(午餐开始, 午餐结束)
        lunch_overtime = max(lunch_minutes - 30, 0) if lunch_minutes else ''

        exception_count = 0
        if late_minutes >= 1: exception_count += 1
        if early_minutes >= 1: exception_count += 1
        if not 上班 or not 下班: exception_count += 1

        writer.writerow([
            date, username, 上班, 下班, 午餐开始, 午餐结束,
            total_work_hours, lunch_hours, overtime_hours,
            late_minutes, early_minutes, exception_count, lunch_overtime
        ])

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8-sig')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='打卡记录统计.csv')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=10000)
