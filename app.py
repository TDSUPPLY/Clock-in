
from flask import Flask, render_template, request, redirect, session, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clockin.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    type = db.Column(db.String(80))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            session['username'] = user.username
            return redirect('/')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if not User.query.filter_by(username=request.form['username']).first():
            user = User(username=request.form['username'], password=request.form['password'])
            db.session.add(user)
            db.session.commit()
            session['username'] = user.username
            return redirect('/')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/api/attendance', methods=['POST'])
def clock_in():
    if 'username' not in session:
        return "Unauthorized", 401
    data = request.get_json()
    exists = Attendance.query.filter_by(username=session['username'], type=data['type']).first()
    if exists:
        return "Already clocked", 400
    record = Attendance(username=session['username'], type=data['type'])
    db.session.add(record)
    db.session.commit()
    return "Success"

@app.route('/export')
def export():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '用户名', '打卡类型', '时间'])
    for row in Attendance.query.all():
        writer.writerow([row.id, row.username, row.type, row.timestamp])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                     download_name='clockin_records.csv', as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()
