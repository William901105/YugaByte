from collections import defaultdict
import datetime
import json
from flask import Flask, request, jsonify
from flask_apscheduler import APScheduler
import psycopg2
import pytz

app = Flask(__name__)


class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
# read host name from host.json file
with open('access_control_system/url.json') as f:
    data = json.load(f)
    HOST = data['host']
    PORT = data['port']
    dbUser = data['dbUser']
    dbPassword = data['dbPassword']
# configurations for database connection
CONFIG = {
    'host': HOST,
    'port': PORT,
    'dbName': 'yugabyte',
    'dbUser': dbUser,
    'dbPassword': dbPassword,
    'sslMode': 'verify-full',
    'sslRootCert': 'root.crt'
}

def get_db_connection():
    return psycopg2.connect(
        host=CONFIG['host'],
        port=CONFIG['port'],
        database=CONFIG['dbName'],
        user=CONFIG['dbUser'],
        password=CONFIG['dbPassword']
    )

def get_yesterday_timestamps():
    tz = pytz.timezone('Asia/Taipei')
    # 台灣現在時間
    now = datetime.datetime.now(tz)

    # 昨天 00:00:00 與 23:59:59
    yesterday_date = now.date() - datetime.timedelta(days=1)
    start_dt = tz.localize(datetime.datetime(yesterday_date.year, yesterday_date.month, yesterday_date.day, 0, 0, 0))
    end_dt = tz.localize(datetime.datetime(yesterday_date.year, yesterday_date.month, yesterday_date.day, 23, 59, 59))

    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    return start_ts, end_ts

def analyze_attendance_and_update_log(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    yesterday_start, yesterday_end = get_yesterday_timestamps()
    yesterday_nine_am = yesterday_start + 9 * 3600

    print("台灣時間 昨日開始 timestamp:", yesterday_start)
    print("台灣時間 昨日結束 timestamp:", yesterday_end)

    # 查詢昨天所有打卡紀錄
    cur.execute(
        'SELECT type, time FROM Record WHERE user_id = %s AND time BETWEEN %s AND %s',
        (user_id, yesterday_start, yesterday_end)
    )
    records = cur.fetchall()
    ins = sorted([t for typ, t in records if typ == 'i'])
    outs = sorted([t for typ, t in records if typ == 'o'])

    log_results = []

    if not ins:
        # 缺席
        log_results.append(("absent", yesterday_start, 8 * 3600))
    else:
        in_time = min(ins)
        if outs:
            out_time = max(outs)
            # 遲到
            late_seconds = max(0, in_time - yesterday_nine_am)
            if late_seconds > 0:
                log_results.append(("late", in_time, late_seconds))
            # 加班
            work_seconds = out_time - in_time
            if work_seconds > 8 * 3600:
                overtime_seconds = work_seconds - 8 * 3600
                log_results.append(("overtime", out_time, overtime_seconds))
        else:
            # 只有進場沒有出場
            log_results.append(("early_leave_or_incomplete", in_time, 0))

    insert_query = "INSERT INTO Log (user_id, type, time, duration) VALUES (%s, %s, %s, %s)"
    for log_type, log_time, log_duration in log_results:
        cur.execute(insert_query, (user_id, log_type, log_time, log_duration))

    conn.commit()
    cur.close()
    conn.close()

    return log_results

# 定時任務
# @scheduler.task('cron', id='daily_analyze', hour=8, minute=0)
# 測試用(分鐘/次)
@scheduler.task('cron', id='daily_analyze', minute='*')
def scheduled_analyze_all_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT user_id FROM Record')
    users = cur.fetchall()
    cur.close()
    conn.close()

    for user in users:
        user_id = user[0]
        analyze_attendance_and_update_log(user_id)
    print("Daily analyze complete at 8:00 AM")

@app.route('/salary', methods=['GET'])
def get_salaries():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT user_id, salary FROM Salary')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([{'user_id': row[0], 'salary': row[1]} for row in rows])

@app.route('/salary/<user_id>', methods=['GET'])
def get_salary(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT user_id, salary FROM Salary WHERE user_id = %s', (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return jsonify({'user_id': row[0], 'salary': row[1]})
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/salary', methods=['POST'])
def add_salary():
    data = request.json
    user_id = data['user_id']
    salary = data['salary']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO Salary (user_id, salary) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET salary = EXCLUDED.salary', (user_id, salary))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Salary updated successfully'})

@app.route('/salary/calculate/<user_id>', methods=['GET'])
def calculate_salary(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT salary FROM Salary WHERE user_id = %s', (user_id,))
    base_salary_row = cur.fetchone()
    if not base_salary_row:
        cur.close()
        conn.close()
        return jsonify({"error": "User not found"}), 404
    base_salary = base_salary_row[0]

    cur.execute('SELECT type, duration FROM Log WHERE user_id = %s', (user_id,))
    logs = cur.fetchall()

    late_penalty = sum(log[1] / 60 * 10 for log in logs if log[0] == 'late')
    absent_penalty = sum(log[1] / 3600 * 100 for log in logs if log[0] == 'absent')
    overtime_bonus = sum(log[1] / 3600 * 200 for log in logs if log[0] == 'overtime')

    final_salary = base_salary + overtime_bonus - late_penalty - absent_penalty

    update_query = 'UPDATE Salary SET salary = %s WHERE user_id = %s'
    cur.execute(update_query, (final_salary, user_id))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "message": "Salary updated successfully",
        "user_id": user_id,
        "base_salary": base_salary,
        "late_penalty": late_penalty,
        "absent_penalty": absent_penalty,
        "overtime_bonus": overtime_bonus,
        "final_salary": final_salary
    })


if __name__ == '__main__':
    app.run(port=5000)