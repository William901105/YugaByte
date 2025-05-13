# all the APIs
# merged by: 113791012
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import time
import hashlib
from functools import wraps
import requests

# read host name from host.json file
with open('access_control_system/url.json') as f:
    data = json.load(f)
    HOST = data['host']
    PORT = data['port']

# configurations for database connection
CONFIG = {
    'host': HOST,
    'port': PORT,
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


def authorization(access_token, user_id):  # authirization main function
    # Connect to the database
    try:
        if CONFIG['sslMode'] != '':
            conn = psycopg2.connect(host=CONFIG['host'], port=CONFIG['port'], database=CONFIG['dbName'],
                                    user=CONFIG['dbUser'], password=CONFIG['dbPassword'],
                                    sslmode=CONFIG['sslMode'], sslrootcert=CONFIG['sslRootCert'],
                                    connect_timeout=10)
        else:
            conn = psycopg2.connect(host=CONFIG['host'], port=CONFIG['port'], database=CONFIG['dbName'],
                                    user=CONFIG['dbUser'], password=CONFIG['dbPassword'],
                                    connect_timeout=10)

    except Exception as e:
        print("Exception while connecting to YugabyteDB")
        print(e)
        return None

    print(">>>> Successfully connected to YugabyteDB!")

    # Create a cursor object using the connection
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Execute a query to check if the access token is valid for the given user ID
    query = """
        SELECT * FROM Author WHERE access_token = %s AND user_id = %s
    """
    cursor.execute(query, (access_token, user_id))

    # Fetch the result of the query
    result = cursor.fetchone()

    # check if the result is none
    if result is None:
        print("Access token is invalid.")
        # Close the cursor and connection
        cursor.close()
        conn.close()
        return "Invalid"

    # get the current time and date
    current_time = time.time()

    # get the time from the result
    token_time = result[3]  # the time is in the forth column

    # check if the token is expired
    if current_time - token_time > 3600:  # 1 hour expiration time
        print("Access token is expired.")
        # Close the cursor and connection
        cursor.close()
        conn.close()
        return "Expired"

    # Close the cursor and connection
    cursor.close()
    conn.close()
    print("Access token is valid.")
    return "Valid"


def update_token(refresh_token, user_id):  # update the token function
    # Connect to the database
    try:
        if CONFIG['sslMode'] != '':
            conn = psycopg2.connect(host=CONFIG['host'], port=CONFIG['port'], database=CONFIG['dbName'],
                                    user=CONFIG['dbUser'], password=CONFIG['dbPassword'],
                                    sslmode=CONFIG['sslMode'], sslrootcert=CONFIG['sslRootCert'],
                                    connect_timeout=10)
        else:
            conn = psycopg2.connect(host=CONFIG['host'], port=CONFIG['port'], database=CONFIG['dbName'],
                                    user=CONFIG['dbUser'], password=CONFIG['dbPassword'],
                                    connect_timeout=10)

    except Exception as e:
        print("Exception while connecting to YugabyteDB")
        print(e)
        return None

    print(">>>> Successfully connected to YugabyteDB!")

    # Create a cursor object using the connection
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # check if the refresh token is valid for the given user ID
    query = """
        SELECT * FROM Author WHERE refresh_token = %s AND user_id = %s
    """
    cursor.execute(query, (refresh_token, user_id))

    # Fetch the result of the query
    result = cursor.fetchone()

    # check if the result is none
    if result is None:
        print("Refresh token is invalid.")
        # Close the cursor and connection
        cursor.close()
        conn.close()
        return None

    # create a new access token and refresh token
    new_access_token = hashlib.sha256(
        (str(result[1]) + str(time.time())).encode()).hexdigest()
    new_refresh_token = hashlib.sha256(
        (str(result[2]) + str(time.time())).encode()).hexdigest()

    # update the access token and refresh token in the database
    update_query = """
        UPDATE Author SET access_token = %s, refresh_token = %s, created_at = %s WHERE user_id = %s
    """
    cursor.execute(update_query, (new_access_token,
                   new_refresh_token, time.time(), user_id))
    conn.commit()

    # Close the cursor and connection
    cursor.close()
    conn.close()
    print("Access token and refresh token updated successfully.")
    return {"new_access_token": new_access_token, "new_refresh_token": new_refresh_token}


# run the app
app = Flask(__name__)
CORS(app)


@app.route('/authorization/authorize', methods=['GET'])
def run_authorization():
    data = request.get_json()
    access_token = data['access_token']
    user_id = data['user_id']

    result = authorization(access_token, user_id)
    if result == "Invalid":
        return jsonify({"result": "Invalid"}), 401
    elif result == "Expired":
        return jsonify({"result": "Expired"}), 401
    else:
        return jsonify({"result": "Valid"}), 200


@app.route('/authorization/refreshToken', methods=['POST'])
def run_update_token():
    data = request.get_json()
    refresh_token = data['refresh_token']
    user_id = data['user_id']

    result = update_token(refresh_token, user_id)
    if result == None:
        return jsonify({"result": "Invalid"}), 401
    else:
        return jsonify(result), 200


@app.route('/record/', methods=['GET', 'POST'])
def record_handler():
    if request.method == 'GET':
        # --- 取資料 Record & EmployeeAccount ---
        try:
            data = request.get_json(force=True)
            ts = data.get('time_start')
            te = data.get('time_end')
        except Exception:
            return jsonify({'error': '請提供 JSON 並含 time_start, time_end'}), 400

        if not isinstance(ts, (int, float)) or not isinstance(te, (int, float)):
            return jsonify({'error': 'time_start 與 time_end 必須為數字'}), 400

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # 原本 Record 表的查詢
            cur.execute(
                'SELECT user_id, type, time FROM Record WHERE time >= %s AND time <= %s',
                (ts, te)
            )
            rows = cur.fetchall()
            record_data = [
                {'user_id': r[0], 'type': r[1], 'time': r[2]}
                for r in rows
            ]

            # 新增：從 EmployeeAccount 表撈取所有 account
            cur.execute('SELECT account FROM employeeaccount')
            acc_rows = cur.fetchall()
            accounts = [r[0] for r in acc_rows]

            conn.close()

            return jsonify({
                'status': 'success',
                'data': record_data,
                'accounts': accounts
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # POST
        # --- 存資料 Log ---
        data = request.get_json() or {}
        uid = data.get('user_id')
        typ = data.get('type')
        tm = data.get('time')
        dur = data.get('duration')

        if uid is None or typ is None or tm is None or dur is None:
            return jsonify({'error': '請提供 user_id, type, time, duration'}), 400

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO Log (user_id, type, time, duration) VALUES (%s, %s, %s, %s)',
                (uid, typ, tm, dur)
            )
            conn.commit()
            conn.close()
            return jsonify({'status': 'success'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/salary/logs', methods=['GET'])  # 查詢日誌
def get_salary_logs():
    # get query parameters from request
    data = request.get_json()
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    print(start_time, end_time)
    # find the data in log table between start_time and end_time
    if start_time and end_time:
        # if start_time and end_time are not float, return 400
        if not isinstance(start_time, (int, float)) or not isinstance(end_time, (int, float)):
            return jsonify({"error": "Invalid time format"}), 400

        command = """
            SELECT user_id, type, time, duration
            FROM log
            WHERE time >= %s AND time <= %s
        """
    else:
        # response miss query parameters
        return jsonify({"error": "Missing time parameters"}), 400

    try:
        conn = get_db_connection()
        curs = conn.cursor()
        curs.execute(command, (start_time, end_time))
        rows = curs.fetchall()

        # convert rows to list of dicts
        logs = [
            {'user_id': r[0], 'type': r[1], 'time': r[2], 'duration': r[3]}
            for r in rows
        ]
        return jsonify(logs), 200
    except Exception as e:
        app.logger.error(f"Log query failed: {str(e)}")
        return jsonify({"error": "Database error"}), 500


@app.route('/salary/update', methods=['POST'])  # 新增或更新薪資
def update_salary():
    """更新薪資"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    user_id = data.get('user_id')
    salary = data.get('salary')
    # 驗證輸入
    if not user_id or not isinstance(salary, (int, float)):
        return jsonify({"error": "Invalid user_id or salary"}), 400

    try:
        conn = get_db_connection()
        curs = conn.cursor()
        # update salary if user_id exists, otherwise insert new record
        curs.execute(
            'SELECT user_id, salary FROM salary WHERE user_id = %s', (user_id,))

        result = curs.fetchall()
        print(result)
        curss = conn.cursor()
        if result:
            # update existing record
            curss.execute(
                'UPDATE salary SET salary = %s WHERE user_id = %s', (salary, user_id,))
        else:
            # insert new record
            curss.execute(
                'INSERT INTO salary (user_id, salary) VALUES (%s, %s)', (user_id, salary,))

        conn.commit()
        return jsonify({"message": "Salary updated successfully"}), 200

    except Exception as e:
        conn.rollback()
        app.logger.error(f"Update failed: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    finally:
        if conn:
            conn.close()


@app.route('/salary/find', methods=['GET'])  # 查詢薪資
def get_user_salary():
    """查詢薪資"""
    user_id = request.get_json().get('user_id')

    try:
        conn = get_db_connection()
        curs = conn.cursor()
        curs.execute(
            'SELECT user_id, salary FROM salary WHERE user_id = %s', (user_id,))
        result = curs.fetchone()

        if result:
            return jsonify({"user_id": result[0], "salary": result[1]}), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        app.logger.error(f"Query failed: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    finally:
        if conn:
            conn.close()


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

        # Connect to the database
        conn = get_db_connection()

        if not conn:
            return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500

        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # Verify if the user is a boss
                cursor.execute("""
                    SELECT * FROM bossaccount WHERE account = %s
                """, (user_id,))
                if not cursor.fetchone():
                    return jsonify({'status': 'error', 'message': '無權限訪問'}), 403

                return func(*args, **kwargs)
        finally:
            conn.close()
    return wrapper


def get_subordinates(boss_id, user_id, cursor):
    """Get all subordinates for a given boss"""
    cursor.execute("""
        SELECT * FROM employeeaccount WHERE boss_id = %s AND account = %s
    """, (boss_id, user_id,))
    result = cursor.fetchone()
    return result is not None


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
            data = request.get_json()
            user_id = data.get('user_id')
            start_time = data.get('start_time')
            end_time = data.get('end_time')

            # Get subordinates for the boss
            subordinates = get_subordinates(boss_id, user_id, cursor)
            if not subordinates:
                return jsonify({'status': 'error', 'message': '無下屬員工'}), 404

            # check if start_time and end_time are valid
            if not start_time or not end_time:
                return jsonify({'status': 'error', 'message': '請提供時間範圍'}), 400

            if user_id:
                # 查詢特定員工的打卡紀錄
                cursor.execute("""
                    SELECT user_id,type,time
                    FROM Record
                    WHERE user_id = %s AND time >= %s AND time <= %s
                """, (user_id, start_time, end_time,))
                employees = cursor.fetchall()
                result = []
                for employee in employees:
                    employee_info = {
                        'user_id': employee[0],
                        'type': employee[1],
                        'time': employee[2]
                    }
                    result.append(employee_info)
                return jsonify({"data": result}), 200

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
            data = request.get_json()
            user_id = data.get('user_id')

            # Get subordinates for the boss
            subordinates = get_subordinates(boss_id, user_id, cursor)
            if not subordinates:
                return jsonify({'status': 'error', 'message': '無下屬員工'}), 404

            if user_id:
                # 查詢特定員工的Salary
                cursor.execute("""
                    SELECT user_id,salary
                    FROM Salary
                    WHERE user_id = %s
                """, (user_id, ))
                salary = cursor.fetchall()
                result = []
                for s in salary:
                    s_info = {
                        'user_id': s[0],
                        'salary': s[1]
                    }
                    result.append(s_info)
                return jsonify({"data": result}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'查詢失敗: {str(e)}'}), 500

    finally:
        conn.close()


@app.route('/employee/register', methods=['POST'])
def employee_register():
    """
    員工註冊
    需要提供 
    account
    password
    boss_id
    """
    data = request.get_json()
    account = data.get('account')
    password = data.get('password')
    boss_id = data.get('boss_id')
    if not account or not password or not boss_id:
        return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400

    # 產生token
    access_token = hashlib.sha256(str(account).encode()).hexdigest()
    refresh_token = hashlib.sha256(
        str(account + "refresh").encode()).hexdigest()
    created_at = time.time()

    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500

    try:
        with conn.cursor() as cursor:
            # 檢查用戶是否已存在
            check_query = "SELECT * FROM employeeaccount WHERE account = %s"
            cursor.execute(check_query, (account,))
            if cursor.fetchone():
                return jsonify({'status': 'error', 'message': '用戶已存在'}), 409

            # 檢查上司是否存在
            check_boss_query = "SELECT * FROM bossaccount WHERE account = %s"
            cursor.execute(check_boss_query, (boss_id,))
            if not cursor.fetchone():
                return jsonify({'status': 'error', 'message': '上司不存在'}), 404

            # 新增用戶
            insert_query = """
                INSERT INTO Author (user_id, access_token, refresh_token, created_at)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (account, access_token,
                           refresh_token, created_at))
            conn.commit()

            # 新增員工帳號
            insert_query = """
                INSERT INTO employeeaccount (account, password, boss_id)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (account, password, boss_id))
            conn.commit()

            # 新增員工薪資
            insert_query = """
                INSERT INTO salary (user_id, salary)
                VALUES (%s, %s)
            """
            cursor.execute(insert_query, (account, 10000))
            conn.commit()

            return jsonify({
                'status': 'success',
                'message': '註冊成功',
                'data': {
                    'account': account,
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'created_at': created_at,
                    'password': password,
                    'boss_id': boss_id
                }
            }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': f'註冊失敗: {str(e)}'}), 500
    finally:
        conn.close()

# 驗證token


def verify_employee_token(header):
    """驗證用戶token"""
    access_token = header.get('Authorization')
    user_id = header.get('X-User-ID')
    if not access_token or not user_id:
        return jsonify({'status': 'error', 'message': '未提供身份認證'}), 401

    # 檢查 token 是否有效
    auth_response = requests.get('http://localhost:5000/authorization/authorize',
                                 json={'access_token': access_token, 'user_id': user_id})

    if auth_response.status_code != 200:
        if auth_response.json().get('result') == 'Expired':
            return jsonify({'status': 'error', 'message': '認證已過期'}), 401
        return jsonify({'status': 'error', 'message': '無效的認證'}), 401
    return jsonify({'status': 'success', 'message': '驗證成功'}), 200


# 查詢打卡記錄
@app.route('/employee/records', methods=['GET'])
def get_employee_records():
    """
    查詢打卡記錄
    需要提供 user_id (員工ID), start_time, end_time (查詢範圍)
    """
    data = request.get_json()
    user_id = data.get('user_id')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    # 驗證token
    header = request.headers
    token_response = verify_employee_token(header)
    if token_response[1] != 200:
        return token_response

    # check if user_id is valid
    header_user_id = header.get('X-User-ID')
    if header_user_id != user_id:
        return jsonify({'status': 'error', 'message': '無權限訪問'}), 403

    # 驗證參數
    if not user_id or not start_time or not end_time:
        return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            query = """
                SELECT user_id, type, time 
                FROM Record 
                WHERE user_id = %s AND time BETWEEN %s AND %s
                ORDER BY time DESC
            """
            cursor.execute(query, (user_id, start_time, end_time,))
            records = cursor.fetchall()

            result = []
            for record in records:
                result.append({
                    'user_id': record['user_id'],
                    'type': record['type'],
                    'time': record['time']
                })

            return jsonify({
                'status': 'success',
                'message': '查詢成功',
                'data': result
            }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'查詢失敗: {str(e)}'}), 500
    finally:
        conn.close()


# 查詢薪資記錄
@app.route('/employee/salary', methods=['GET'])
def get_employee_salary():
    """
    查詢薪資記錄
    需要提供 user_id (員工ID)
    """
    data = request.get_json()
    user_id = data.get('user_id')

    # 驗證token
    header = request.headers
    token_response = verify_employee_token(header)
    if token_response[1] != 200:
        return token_response

    # check if user_id is valid
    header_user_id = header.get('X-User-ID')
    if header_user_id != user_id:
        return jsonify({'status': 'error', 'message': '無權限訪問'}), 403

    # 驗證參數
    if not user_id:
        return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            query = """
                SELECT user_id, salary
                FROM Salary 
                WHERE user_id = %s
            """
            cursor.execute(query, (user_id, ))
            records = cursor.fetchall()

            result = []
            for record in records:
                result.append({
                    'user_id': record['user_id'],
                    'salary': record['salary']
                })

            return jsonify({
                'status': 'success',
                'message': '查詢成功',
                'data': result
            }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'查詢失敗: {str(e)}'}), 500
    finally:
        conn.close()


# test
if __name__ == "__main__":
    # run the app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
