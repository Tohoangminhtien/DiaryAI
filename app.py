from flask import Flask, render_template, request, url_for, redirect, session
from datetime import datetime, timedelta
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.permanent_session_lifetime = timedelta(minutes=10)


@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        df = pd.read_csv('account/accounts.csv')
        account = df['account'].to_list()
        password = df['password'].to_list()

        user_acc = request.form['username']
        user_pass = request.form['password']

        for ac, pa in zip(account, password):
            if user_acc == str(ac) and user_pass == str(pa):
                # Tự đọng xoa session
                session.permanent = True
                session['user'] = user_acc
                return redirect(url_for('calendar'))

        return redirect(url_for('login'))


@app.route('/')
def calendar():
    check_login()

    month = request.args.get('month', default=datetime.now().month, type=int)
    year = request.args.get('year', default=datetime.now().year, type=int)

    # Chuyển tháng
    if 'next' in request.args:
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
    elif 'prev' in request.args:
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1

    current_date = datetime(year, month, 1)
    return render_template('calendar.html', current_date=current_date, timedelta=timedelta)


def check_login():
    if 'user' not in session:
        return redirect(url_for('login'))


@app.route('/direct')
def router():
    # Kiểm tra thời gian
    day = request.args.get('day')
    month = request.args.get('month')
    year = request.args.get('year')

    # Kiểm tra user
    user = session['user']

    # Nếu file đã tồn tại thì tiến hành đọc
    if os.path.exists(f"user/{user}/{day}_{month}_{year}.txt"):
        return redirect(url_for('read_diary', day=day, month=month, year=year))

    # Nếu chưa có thì xét các yếu tố
    input_date_str = f"{day}/{month}/{year}"
    input_date = datetime.strptime(input_date_str, "%d/%m/%Y")
    current_date = datetime.now().date()
    input_date_only = input_date.date()

    # Kiểm tra xem ngày nhập vào đã vượt qua ngày hiện tại chưa
    if input_date_only < current_date:
        return "You forgot to write this diary :( "

    elif input_date_only == current_date:
        session['day'] = day
        session['month'] = month
        session['year'] = year
        return redirect(url_for('write_diary'))

    else:
        return "The date has not passed yet."


@app.route('/read')
def read_diary():
    check_login()

    day = request.args.get('day')
    month = request.args.get('month')
    year = request.args.get('year')

    file_path = f"user/{session['user']}/{day}_{month}_{year}.txt"
    with open(file_path, 'r', encoding='utf-8') as file:
        raw = file.read()
        content = raw.replace('\n', '<br>')
    return render_template('read.html', content=content, time=f'{day}/{month}/{year}')


@app.route('/write', methods=['GET', 'POST'])
def write_diary():
    check_login()

    if request.method == 'GET':
        return render_template('write.html')

    else:
        content = request.form['content']
        day = session['day']
        month = session['month']
        year = session['year']

        file_path = f"user/{session['user']}/{day}_{month}_{year}.txt"

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

        session.pop('day', None)
        session.pop('month', None)
        session.pop('year', None)
        return redirect(url_for('calendar'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.errorhandler(Exception)
def handle_exception(error):
    return render_template('error.html', error_code=500, message="Something went wrong!"), 500


if __name__ == '__main__':
    app.run(debug=True)
