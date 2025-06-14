
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

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/', methods=['GET'])
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
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/attendance', methods=['POST'])
def attendance():
    if 'username' not in session:
        return jsonify({"error": "not logged in"}), 401
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
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '用户名', '打卡类型', '日期时间'])
    for entry in Attendance.query.order_by(Attendance.timestamp.desc()).all():
        writer.writerow([entry.id, entry.username, entry.type, entry.timestamp])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='attendance.csv')

if __name__ == '__main__':
    app.run(debug=True)
