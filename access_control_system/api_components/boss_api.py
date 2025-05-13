import json
import psycopg2
import psycopg2.extras
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from functools import wraps
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 從 url.json 讀取資料庫連線設定
with open('access_control_system/url.json') as f:
    db_config = json.load(f)

# 資料庫連線設定
CONFIG = {
    'host': db_config['host'],
    'port': db_config['port'],
    'dbName': 'yugabyte',
    'dbUser': 'yugabyte',
    'dbPassword': 'yugabyte',
    'sslMode': '',
    'sslRootCert': ''
}


def get_db_connection():
    return psycopg2.connect(
        host=CONFIG['host'],
        port=CONFIG['port'],
        database=CONFIG['dbName'],
        user=CONFIG['dbUser'],
        password=CONFIG['dbPassword'],
        sslrootcert=CONFIG['sslRootCert'])


def verify_boss_access(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        access_token = request.headers.get('Authorization')
        user_id = request.headers.get('X-User-ID')

        if not access_token or not user_id:
            return jsonify({'status': 'error', 'message': '未提供身份認證'}), 401

        # 先檢查 token 是否有效
        auth_response = requests.get('http://localhost:5000/authorization/authorize',
                                     json={'access_token': access_token, 'user_id': user_id})

        if auth_response.status_code != 200:
            if auth_response.json().get('result') == 'Expired':
                return jsonify({'status': 'error', 'message': '認證已過期'}), 401
            return jsonify({'status': 'error', 'message': '無效的認證'}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500

        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # Verify if the user is a boss
                cursor.execute("""
                    SELECT role FROM Author WHERE user_id = %s AND role = 'boss'
                """, (user_id,))
                if not cursor.fetchone():
                    return jsonify({'status': 'error', 'message': '無權限訪問'}), 403

                return func(*args, **kwargs)
        finally:
            conn.close()
    return wrapper


def get_subordinates(boss_id, cursor):
    """Get all subordinates for a given boss"""
    cursor.execute("""
        SELECT user_id FROM Author WHERE boss_id = %s
    """, (boss_id,))
    return [row['user_id'] for row in cursor.fetchall()]


@app.route('/boss/subordinate_record', methods=['GET'])
@verify_boss_access
def get_subordinate_record():
    """
    BOSS API：查詢員工的打卡時間和薪資。
    可以選擇查詢所有員工或特定員工，並可指定時間範圍。
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            boss_id = request.headers.get('X-User-ID')
            user_id = request.args.get('user_id')
            start_date = request.args.get('start_time')
            end_date = request.args.get('end_time')

            # Get subordinates for the boss
            subordinates = get_subordinates(boss_id, cursor)
            if not subordinates:
                return jsonify({'status': 'error', 'message': '無下屬員工'}), 404

            # Build the date filter condition
            date_condition = ""
            date_params = []
            if start_date and end_date:
                date_condition = "AND r.time BETWEEN %s AND %s"
                try:
                    date_params = [datetime.strptime(start_date, '%Y-%m-%d'),
                                   datetime.strptime(end_date, '%Y-%m-%d')]
                except ValueError:
                    return jsonify({'status': 'error', 'message': '日期格式錯誤，請使用 YYYY-MM-DD 格式'}), 400

            if user_id:
                # Verify if the requested employee is a subordinate
                if user_id not in subordinates:
                    return jsonify({'status': 'error', 'message': '無權限查看該員工資料'}), 403

                # 查詢特定員工
                cursor.execute("""
                    SELECT a.user_id, s.salary
                    FROM Author a
                    JOIN Salary s ON a.user_id = s.user_id
                    WHERE a.user_id = %s AND a.boss_id = %s
                """, (user_id, boss_id))
                employees = cursor.fetchall()

                # 查詢特定員工的打卡紀錄
                clock_records = {}
                query = """
                    SELECT r.user_id, r.type, r.time
                    FROM Record r
                    WHERE r.type IN ('i', 'o') 
                    AND r.user_id = %s 
                """ + date_condition + """
                    ORDER BY r.time DESC
                """
                params = [user_id] + date_params
                cursor.execute(query, tuple(params))
                records = cursor.fetchall()

            else:
                # 查詢所有下屬員工
                cursor.execute("""
                    SELECT a.user_id, s.salary
                    FROM Author a
                    JOIN Salary s ON a.user_id = s.user_id
                    WHERE a.boss_id = %s
                """, (boss_id,))
                employees = cursor.fetchall()

                # 查詢所有下屬員工的打卡紀錄
                clock_records = {}
                query = """
                    SELECT r.user_id, r.type, r.time
                    FROM Record r
                    WHERE r.type IN ('i', 'o') 
                    AND r.user_id = ANY(%s)
                """ + date_condition + """
                    ORDER BY r.time DESC
                """
                params = [subordinates] + date_params
                cursor.execute(query, tuple(params))
                records = cursor.fetchall()

            # Process clock records
            for record in records:
                user_id = record['user_id']
                clock_type = '上班' if record['type'] == 'i' else '下班'
                if user_id not in clock_records:
                    clock_records[user_id] = {'上班': [], '下班': []}
                clock_records[user_id][clock_type].append(record['time'])

            # 整合員工資料
            result = []
            for employee in employees:
                employee_info = {
                    'user_id': employee['user_id'],
                    'salary': employee['salary'],
                    'clock_records': clock_records.get(employee['user_id'], {'上班': [], '下班': []})
                }
                result.append(employee_info)

            return jsonify({
                'status': 'success',
                'message': '查詢成功',
                'data': result
            }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'查詢失敗: {str(e)}'}), 500

    finally:
        conn.close()


@app.route('/boss/subordinate_salary', methods=['GET'])
@verify_boss_access
def subordinate_salary():
    """Verify if an employee is a subordinate of the requesting boss"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            boss_id = request.headers.get('X-User-ID')
            employee_id = request.args.get('employee_id')

            if not employee_id:
                return jsonify({'status': 'error', 'message': '未提供員工 ID'}), 400

            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM Author 
                    WHERE user_id = %s AND boss_id = %s
                ) as is_subordinate
            """, (employee_id, boss_id))

            result = cursor.fetchone()
            return jsonify({
                'status': 'success',
                'is_subordinate': result['is_subordinate']
            }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'查詢失敗: {str(e)}'}), 500

    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
