# app.py

from flask import Flask, render_template, request, redirect, session, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os, io, csv
from collections import defaultdict

# 加载 .env
load_dotenv()

app = Flask(__name__)
app.secret_key = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ✅ 修正表名为小写，避免 Supabase 自动转小写引发数据丢失
class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)

class attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50))
    date = db.Column(db.String(20))

# 马来西亚时间
def malaysia_now():
    return datetime.utcnow() + timedelta(hours=8)

@app.route('/')
def home():
    if 'username' not in session:
        return redirect('/login')
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        u = user.query.filter_by(username=username).first()
        if u:
            session['username'] = username
            return redirect('/')
        else:
            return "用户不存在，请先注册"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        if not user.query.filter_by(username=username).first():
            db.session.add(user(username=username))
            db.session.commit()
            return redirect('/login')
        else:
            return "用户已存在，请返回登录"
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/attendance', methods=['POST'])
def attendance_api():
    if 'username' not in session:
        return jsonify({"error": "未登录"}), 401

    data = request.get_json()
    t = data['type']
    now = malaysia_now()
    today = now.strftime('%Y-%m-%d')
    uname = session['username']

    if t in ['上班打卡', '午餐开始', '加班开始']:
        exists = attendance.query.filter_by(username=uname, type=t, date=today).first()
        if exists:
            return jsonify({"message": f"{t} 已打卡（首次记录为准）"})
        db.session.add(attendance(username=uname, type=t, date=today, timestamp=now))
        db.session.commit()
        return jsonify({"message": f"{t} 打卡成功"})

    elif t in ['下班打卡', '午餐结束', '加班结束']:
        attendance.query.filter_by(username=uname, type=t, date=today).delete()
        db.session.add(attendance(username=uname, type=t, date=today, timestamp=now))
        db.session.commit()

        if t == '午餐结束':
            lunch = attendance.query.filter_by(username=uname, type='午餐开始', date=today).first()
            if lunch:
                dur = (now - lunch.timestamp).total_seconds() / 60
                if dur > 40:
                    return jsonify({"message": "午餐超时（超过40分钟）"})
                elif dur > 30:
                    return jsonify({"message": "午餐已超过30分钟，请尽快返回岗位"})

        return jsonify({"message": f"{t} 打卡成功（记录以最后一次为准）"})

    return jsonify({"error": "无效的打卡类型"}), 400

@app.route('/export')
def export():
    if 'username' not in session:
        return redirect('/login')

    records = attendance.query.order_by(attendance.username, attendance.date, attendance.timestamp).all()
    grouped = defaultdict(dict)
    for r in records:
        key = (r.username, r.date)
        grouped[key][r.type] = r.timestamp.strftime('%H:%M:%S')

    def calc_minutes(s, e):
        try:
            return round((datetime.strptime(e, '%H:%M:%S') - datetime.strptime(s, '%H:%M:%S')).total_seconds() / 60)
        except:
            return 0

    def calc_hours(s, e):
        return round(calc_minutes(s, e) / 60, 2) if s and e else ''

    def get_expect_time(date, is_start):
        weekday = datetime.strptime(date, '%Y-%m-%d').weekday()
        return '09:00:00' if is_start else ('16:00:00' if weekday == 5 else '17:30:00')

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['日期', '用户名', '上班时间', '下班时间', '午餐开始', '午餐结束',
                     '总工时(h)', '午餐时长(h)', '加班时长(h)',
                     '迟到(min)', '早退(min)', '异常次数', '午餐超时(min)'])

    for (uname, date), log in grouped.items():
        上班, 下班 = log.get('上班打卡', ''), log.get('下班打卡', '')
        午餐开始, 午餐结束 = log.get('午餐开始', ''), log.get('午餐结束', '')
        加班开始, 加班结束 = log.get('加班开始', ''), log.get('加班结束', '')

        work = calc_hours(上班, 下班)
        lunch = calc_hours(午餐开始, 午餐结束)
        ot = calc_hours(加班开始, 加班结束)
        total = round((work or 0) - (lunch or 0.5), 2) if work else ''

        late = calc_minutes(get_expect_time(date, True), 上班) if 上班 else 0
        early = calc_minutes(下班, get_expect_time(date, False)) if 下班 else 0
        lunch_m = calc_minutes(午餐开始, 午餐结束)
        lunch_overtime = max(lunch_m - 30, 0) if lunch_m else ''

        ex = int(late > 0) + int(early > 0) + int(not 上班 or not 下班)

        writer.writerow([date, uname, 上班, 下班, 午餐开始, 午餐结束,
                         total, lunch, ot, late, early, ex, lunch_overtime])

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8-sig')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='打卡记录.csv')

# ✅ 支持 Render 自动端口
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
