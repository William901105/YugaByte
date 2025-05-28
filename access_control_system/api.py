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


FLAG = False  # set to True if you want to use the backup database

# read host name from url.json file
with open('access_control_system/url.json') as f:
    data = json.load(f)
    HOST = data['host']
    PORT = data['port']

# read host name from backup_url.json file
with open('access_control_system/backup_url.json') as f:
    data = json.load(f)
    BACKUPHOST = data['host']
    BACKUPPORT = data['port']

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

# get the database connection


def get_db_connection():
    return psycopg2.connect(
        host=CONFIG['host'],
        port=CONFIG['port'],
        database=CONFIG['dbName'],
        user=CONFIG['dbUser'],
        password=CONFIG['dbPassword'],
        sslrootcert=CONFIG['sslRootCert'])

# get the backup database connection


def get_backup_db_connection():
    print("Using Backup YugabyteDB")
    return psycopg2.connect(
        host=BACKUPHOST,
        port=BACKUPPORT,
        database=CONFIG['dbName'],
        user=CONFIG['dbUser'],
        password=CONFIG['dbPassword'],
        sslrootcert=CONFIG['sslRootCert'])


def authorization(access_token, user_id):  # authirization main function
    # Connect to the database
    try:
        conn = get_db_connection()

    except Exception as e:
        print("Exception while connecting to Main YugabyteDB")
        print(e)
        try:
            conn = get_backup_db_connection()
        except Exception as e:
            print("Exception while connecting to Backup YugabyteDB")
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
        conn = get_db_connection()
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
        # update in the backup database
        try:
            backup_conn = get_backup_db_connection()
            backup_cursor = backup_conn.cursor(
                cursor_factory=psycopg2.extras.DictCursor)
            backup_cursor.execute(update_query, (new_access_token,
                                                 new_refresh_token, time.time(), user_id))
            backup_conn.commit()
            backup_cursor.close()
            backup_conn.close()
            print("Backup successfully.")
        except Exception as e:
            print("Exception while updating in Backup YugabyteDB")
            print(e)

        cursor.execute(update_query, (new_access_token,
                                      new_refresh_token, time.time(), user_id))
        conn.commit()
        # Close the cursor and connection
        cursor.close()
        conn.close()
        print("Access token and refresh token updated successfully.")
        return {"new_access_token": new_access_token, "new_refresh_token": new_refresh_token}

    except Exception as e:
        conn = get_backup_db_connection()
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
        # update in the backup database

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
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-User-ID"]
}}, supports_credentials=True)


# finish backup database


@app.route('/authorization/authorize', methods=['GET'])
def run_authorization():
    try:
        # 嘗試從 JSON 請求體中獲取數據
        data = request.get_json(silent=True)
        if data and 'access_token' in data and 'user_id' in data:
            access_token = data['access_token']
            user_id = data['user_id']
        else:
            # 如果 JSON 請求體中沒有數據，嘗試從 URL 參數中獲取
            access_token = request.args.get('access_token')
            user_id = request.args.get('user_id')

            # 如果 URL 參數中也沒有數據，嘗試從 HTTP 頭部中獲取
            if not access_token or not user_id:
                access_token = request.headers.get('Authorization')
                user_id = request.headers.get('X-User-ID')

        if not access_token or not user_id:
            return jsonify({"result": "Invalid", "message": "未提供認證信息"}), 401

        result = authorization(access_token, user_id)
        if result == "Invalid":
            return jsonify({"result": "Invalid"}), 401
        elif result == "Expired":
            return jsonify({"result": "Expired"}), 401
        else:
            return jsonify({"result": "Valid"}), 200
    except Exception as e:
        print(f"認證過程中發生錯誤: {e}")
        return jsonify({"result": "Error", "message": str(e)}), 500


# finish backup database


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

# finish backup database


@app.route('/record', methods=['GET', 'POST'])
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
            # sorting by time
            cur.execute(
                'SELECT user_id, type, time FROM Record WHERE time >= %s AND time <= %s ORDER BY time DESC',
                (ts, te)  # time_start, time_end
            )
            rows = cur.fetchall()
            record_data = [
                {'user_id': r[0], 'type': r[1], 'time': r[2]}
                for r in rows
            ]

            # 新增：從 EmployeeAccount 表撈取所有 account
            cur.execute('SELECT account,boss_id FROM employeeaccount')
            acc_rows = cur.fetchall()
            accounts = [{"employee": r[0], "boss": r[1]} for r in acc_rows]

            conn.close()

            return jsonify({
                'status': 'success',
                'data': record_data,
                'accounts': accounts
            })
        except Exception as e:
            # using backup database
            print("Exception while inserting into Main YugabyteDB")
            print(e)
            try:
                backup_conn = get_backup_db_connection()
                backup_cur = backup_conn.cursor()
                # sorting by time
                backup_cur.execute(
                    'SELECT user_id, type, time FROM Record WHERE time >= %s AND time <= %s ORDER BY time DESC',
                    (ts, te)  # time_start, time_end
                )
                rows = backup_cur.fetchall()
                record_data = [
                    {'user_id': r[0], 'type': r[1], 'time': r[2]}
                    for r in rows
                ]

                # 新增：從 EmployeeAccount 表撈取所有 account
                backup_cur.execute(
                    'SELECT account,boss_id FROM employeeaccount')
                acc_rows = backup_cur.fetchall()
                accounts = [{"employee": r[0], "boss": r[1]} for r in acc_rows]

                backup_conn.close()

                return jsonify({
                    'status': 'success',
                    'data': record_data,
                    'accounts': accounts
                })
            except Exception as e:
                print("Exception while inserting into Backup YugabyteDB")
                print(e)
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
            # backup database
            try:
                backup_conn = get_backup_db_connection()
                backup_cur = backup_conn.cursor()
                backup_cur.execute(
                    'INSERT INTO Log (user_id, type, time, duration) VALUES (%s, %s, %s, %s)',
                    (uid, typ, tm, dur)
                )
                backup_conn.commit()
                backup_conn.close()
                print("Backup successfully.")
            except Exception as e:
                print("Exception while inserting into Backup YugabyteDB")
                print(e)
            conn.commit()
            conn.close()
            return jsonify({'status': 'success'}), 201
        except Exception as e:
            # using backup database
            print("Exception while inserting into Main YugabyteDB")
            print(e)
            try:
                backup_conn = get_backup_db_connection()
                backup_cur = backup_conn.cursor()
                backup_cur.execute(
                    'INSERT INTO Log (user_id, type, time, duration) VALUES (%s, %s, %s, %s)',
                    (uid, typ, tm, dur)
                )
                backup_conn.commit()
                backup_conn.close()
                print("Write in Backup Database successfully.")
                return jsonify({'status': 'success'}), 201
            except Exception as e:
                print("Exception while inserting into Backup YugabyteDB")
                print(e)
                return jsonify({'error': str(e)}), 500

# finish backup database


@app.route('/salary/logs', methods=['POST'])  # 查詢日誌
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
        # using backup database
        print("Exception while querying from Main YugabyteDB")
        print(e)
        try:
            backup_conn = get_backup_db_connection()
            backup_cur = backup_conn.cursor()
            backup_cur.execute(command, (start_time, end_time))
            rows = backup_cur.fetchall()

            # convert rows to list of dicts
            logs = [
                {'user_id': r[0], 'type': r[1], 'time': r[2], 'duration': r[3]}
                for r in rows
            ]
            return jsonify(logs), 200
        except Exception as e:
            print("Exception while querying from Backup YugabyteDB")
            print(e)
            return jsonify({"error": "Database error"}), 500

# finish backup database


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
        conn.commit()
        conn.close()

        if result:
            # update existing record
            conn = get_db_connection()
            curs = conn.cursor()
            curs.execute(
                'UPDATE salary SET salary = %s WHERE user_id = %s', (salary, user_id,))
            conn.commit()
            conn.close()
            print("Salary updated successfully in Main YugabyteDB.")
            # backup database
            try:
                backup_conn = get_backup_db_connection()
                backup_cur = backup_conn.cursor()
                backup_cur.execute(
                    'UPDATE salary SET salary = %s WHERE user_id = %s', (salary, user_id,))
                backup_conn.commit()
                backup_conn.close()
                print("Backup successfully.")
            except Exception as e:
                print("Exception while updating in Backup YugabyteDB")
                print(e)
        else:
            # insert new record
            conn = get_db_connection()
            curs = conn.cursor()
            curs.execute(
                'INSERT INTO salary (user_id, salary) VALUES (%s, %s)', (user_id, salary,))
            conn.commit()
            conn.close()
            # backup database
            try:
                backup_conn = get_backup_db_connection()
                backup_cur = backup_conn.cursor()
                backup_cur.execute(
                    'INSERT INTO salary (user_id, salary) VALUES (%s, %s)', (user_id, salary,))
                backup_conn.commit()
                backup_conn.close()
                print("Backup successfully.")
            except Exception as e:
                print("Exception while updating in Backup YugabyteDB")
                print(e)

        print("Salary updated successfully in Main YugabyteDB.")
        return jsonify({"message": "Salary updated successfully"}), 200

    except Exception as e:
        # using backup database
        print("Exception while updating in Main YugabyteDB")
        print(e)
        try:
            backup_conn = get_backup_db_connection()
            backup_cur = backup_conn.cursor()
            # update salary if user_id exists, otherwise insert new record
            backup_cur.execute(
                'SELECT user_id, salary FROM salary WHERE user_id = %s', (user_id,))

            result = backup_cur.fetchall()
            curss = backup_conn.cursor()
            if result:
                # update existing record
                curss.execute(
                    'UPDATE salary SET salary = %s WHERE user_id = %s', (salary, user_id,))
                backup_conn.commit()
                backup_conn.close()
                print("Using Backup successfully.")
            else:
                # insert new record
                curss.execute(
                    'INSERT INTO salary (user_id, salary) VALUES (%s, %s)', (user_id, salary,))
                backup_conn.commit()
                backup_conn.close()
                print("Using Backup successfully.")
            return jsonify({"message": "Salary updated successfully"}), 200

        except Exception as e:
            print("Exception while updating in Backup YugabyteDB")
            print(e)
            return jsonify({"error": "Database error"}), 500


# finish backup database


@app.route('/salary/find', methods=['POST'])  # 查詢薪資
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
        # using backup database
        print("Exception while querying from Main YugabyteDB")
        print(e)
        try:
            backup_conn = get_backup_db_connection()
            backup_cur = backup_conn.cursor()
            backup_cur.execute(
                'SELECT user_id, salary FROM salary WHERE user_id = %s', (user_id,))
            result = backup_cur.fetchone()

            if result:
                print("Using Backup successfully.")
                return jsonify({"user_id": result[0], "salary": result[1]}), 200
            else:
                print("Using Backup successfully.")
                return jsonify({"error": "User not found"}), 404

        except Exception as e:
            print("Exception while querying from Backup YugabyteDB")
            print(e)
            return jsonify({"error": "Database error"}), 500


# finish backup database


def verify_boss_access(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        access_token = request.headers.get('Authorization')
        user_id = request.headers.get('X-User-ID')

        if not access_token or not user_id:
            return jsonify({'status': 'error', 'message': '未提供身份認證'}), 401

        # 直接調用 authorization 函數，而不是通過 HTTP 請求
        auth_result = authorization(access_token, user_id)

        if auth_result != "Valid":
            if auth_result == "Expired":
                return jsonify({'status': 'error', 'message': '認證已過期'}), 401
            return jsonify({'status': 'error', 'message': '無效的認證'}), 401

        # Connect to the database
        try:
            conn = get_db_connection()
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # Verify if the user is a boss
                cursor.execute("""
                    SELECT * FROM bossaccount WHERE account = %s
                """, (user_id,))
                if not cursor.fetchone():
                    return jsonify({'status': 'error', 'message': '無權限訪問'}), 403

                return func(*args, **kwargs)
        except Exception as e:
            print("Exception while connecting to Main YugabyteDB")
            print(e)
            conn = get_backup_db_connection()
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


def get_subordinates(boss_id, cursor):
    """Get all subordinates for a given boss"""
    cursor.execute("""
        SELECT account FROM employeeaccount WHERE boss_id = %s
    """, (boss_id,))
    return [row[0] for row in cursor.fetchall()]

# finish backup database


@app.route('/boss/subordinate_record', methods=['POST'])
@verify_boss_access
def get_subordinate_record():
    """
    BOSS API：查詢員工的打卡時間和薪資。
    可以選擇查詢所有員工或特定員工，並可指定時間範圍。
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                boss_id = request.headers.get('X-User-ID')
                data = request.get_json()
                user_id = data.get('user_id')
                start_time = data.get('start_time')
                end_time = data.get('end_time')

                # 獲取所有下屬
                subordinates = get_subordinates(boss_id, cursor)

                # 檢查請求的用戶是否為下屬
                if not subordinates or user_id not in subordinates:
                    return jsonify({'status': 'error', 'message': '無權限查詢該員工或該員工不存在'}), 403

                # 檢查時間範圍是否有效
                if not start_time or not end_time:
                    return jsonify({'status': 'error', 'message': '請提供時間範圍'}), 400

                # 查詢特定員工的打卡紀錄
                cursor.execute("""
                    SELECT user_id, type, time
                    FROM Record
                    WHERE user_id = %s AND time >= %s AND time <= %s
                """, (user_id, start_time, end_time,))

                records = cursor.fetchall()
                result = []
                for record in records:
                    record_info = {
                        'user_id': record[0],
                        'type': record[1],
                        'time': record[2]
                    }
                    result.append(record_info)

                return jsonify({"status": "success", "data": result}), 200

        except Exception as e:
            return jsonify({'status': 'error', 'message': f'查詢失敗: {str(e)}'}), 500
    except Exception as e:
        print("Exception while connecting to Main YugabyteDB")
        print(e)
        # 使用備用資料庫
        try:
            backup_conn = get_backup_db_connection()
            with backup_conn.cursor() as backup_cursor:
                boss_id = request.headers.get('X-User-ID')
                data = request.get_json()
                user_id = data.get('user_id')
                start_time = data.get('start_time')
                end_time = data.get('end_time')

                # 獲取所有下屬
                subordinates = get_subordinates(boss_id, backup_cursor)

                # 檢查請求的用戶是否為下屬
                if not subordinates or user_id not in subordinates:
                    return jsonify({'status': 'error', 'message': '無權限查詢該員工或該員工不存在'}), 403

                # 檢查時間範圍是否有效
                if not start_time or not end_time:
                    return jsonify({'status': 'error', 'message': '請提供時間範圍'}), 400

                # 查詢特定員工的打卡紀錄
                backup_cursor.execute("""
                    SELECT user_id, type, time
                    FROM Record
                    WHERE user_id = %s AND time >= %s AND time <= %s
                """, (user_id, start_time, end_time,))

                records = backup_cursor.fetchall()
                result = []
                for record in records:
                    record_info = {
                        'user_id': record[0],
                        'type': record[1],
                        'time': record[2]
                    }
                    result.append(record_info)

                print("Using Backup Successfully")
                return jsonify({"status": "success", "data": result}), 200

        except Exception as e:
            print("Exception while connecting to Backup YugabyteDB")
            print(e)
            return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500


# finish backup database


@app.route('/boss/subordinate_salary', methods=['POST'])
@verify_boss_access
def subordinate_salary():
    """查詢下屬員工的薪資"""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            boss_id = request.headers.get('X-User-ID')
            data = request.get_json()
            user_id = data.get('user_id')

            # 獲取所有下屬
            subordinates = get_subordinates(boss_id, cursor)

            # 檢查請求的用戶是否為下屬
            if not subordinates or user_id not in subordinates:
                return jsonify({'status': 'error', 'message': '無權限查詢該員工或該員工不存在'}), 403

            # 查詢特定員工的薪資
            cursor.execute("""
                SELECT user_id, salary
                FROM Salary
                WHERE user_id = %s
            """, (user_id, ))

            salary_records = cursor.fetchall()
            result = []
            for record in salary_records:
                salary_info = {
                    'user_id': record[0],
                    'salary': record[1]
                }
                result.append(salary_info)

            return jsonify({"status": "success", "data": result}), 200

    except Exception as e:
        print("Exception while connecting to Main YugabyteDB")
        print(e)
        # 使用備用資料庫
        try:
            backup_conn = get_backup_db_connection()
            with backup_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                boss_id = request.headers.get('X-User-ID')
                data = request.get_json()
                user_id = data.get('user_id')

                # 獲取所有下屬
                subordinates = get_subordinates(boss_id, cursor)

                # 檢查請求的用戶是否為下屬
                if not subordinates or user_id not in subordinates:
                    return jsonify({'status': 'error', 'message': '無權限查詢該員工或該員工不存在'}), 403

                # 查詢特定員工的薪資
                cursor.execute("""
                    SELECT user_id, salary
                    FROM Salary
                    WHERE user_id = %s
                """, (user_id, ))

                salary_records = cursor.fetchall()
                result = []
                for record in salary_records:
                    salary_info = {
                        'user_id': record[0],
                        'salary': record[1]
                    }
                    result.append(salary_info)

                print("Using Backup Successfully")
                return jsonify({"status": "success", "data": result}), 200

        except Exception as backup_e:
            print("Exception while connecting to Backup YugabyteDB")
            print(backup_e)
            return jsonify({'status': 'error', 'message': f'查詢失敗: {str(e)}，備份資料庫也失敗: {str(backup_e)}'}), 500
    finally:
        if conn:
            conn.close()

# finish backup database


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

    try:
        conn = get_db_connection()
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

            # backup database
            try:
                backup_conn = get_backup_db_connection()
                backup_cursor = backup_conn.cursor()

                # 新增用戶
                insert_query = """
                    INSERT INTO Author (user_id, access_token, refresh_token, created_at)
                    VALUES (%s, %s, %s, %s)
                """
                backup_cursor.execute(insert_query, (account, access_token,
                                                     refresh_token, created_at))
                backup_conn.commit()

                # 新增員工帳號
                insert_query = """
                    INSERT INTO employeeaccount (account, password, boss_id)
                    VALUES (%s, %s, %s)
                """
                backup_cursor.execute(insert_query,
                                      (account, password, boss_id))
                backup_conn.commit()

                # 新增員工薪資
                insert_query = """
                    INSERT INTO salary (user_id, salary)
                    VALUES (%s, %s)
                """
                backup_cursor.execute(insert_query, (account, 10000))
                backup_conn.commit()
                backup_conn.close()
                print("Backup successfully.")
            except Exception as e:
                print("Exception while inserting into Backup YugabyteDB")
                print(e)

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
        conn = get_backup_db_connection()
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
            print("Using Backup Successfully")
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

        return jsonify({'status': 'error', 'message': f'註冊失敗: {str(e)}'}), 500
    finally:
        conn.close()

# 驗證token

# no need to backup database


def verify_employee_token(header):
    """驗證用戶token"""
    access_token = header.get('Authorization')
    user_id = header.get('X-User-ID')
    if not access_token or not user_id:
        return jsonify({'status': 'error', 'message': '未提供身份認證'}), 401

    # 直接調用 authorization 函數，而不是通過 HTTP 請求
    auth_result = authorization(access_token, user_id)

    if auth_result != "Valid":
        if auth_result == "Expired":
            return jsonify({'status': 'error', 'message': '認證已過期'}), 401
        return jsonify({'status': 'error', 'message': '無效的認證'}), 401
    return jsonify({'status': 'success', 'message': '驗證成功'}), 200

# finish backup database
# 查詢打卡記錄


@app.route('/employee/records', methods=['GET', 'POST'])
def employee_records():
    """
    GET: 查詢打卡記錄
    POST: 新增打卡記錄到 Record 表
    """
    # 驗證 token
    header = request.headers
    token_response = verify_employee_token(header)
    if token_response[1] != 200:
        return token_response

    # 現有的 GET 方法處理
    if request.method == 'GET':
        data = request.get_json()
        user_id = data.get('user_id')
        start_time = data.get('time_start')
        end_time = data.get('time_end')

        # check if user_id is valid
        header_user_id = header.get('X-User-ID')
        if header_user_id != user_id:
            return jsonify({'status': 'error', 'message': '無權限訪問'}), 403

        # 驗證參數
        if not user_id or not start_time or not end_time:
            return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400

        conn = None  # 初始化 conn 變數
        try:
            conn = get_db_connection()
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
            try:
                conn = get_backup_db_connection()
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as backup_cursor:
                    query = """
                        SELECT user_id, type, time 
                        FROM Record 
                        WHERE user_id = %s AND time BETWEEN %s AND %s
                        ORDER BY time DESC
                    """
                    backup_cursor.execute(query, (user_id, start_time, end_time,))
                    records = backup_cursor.fetchall()

                    result = []
                    for record in records:
                        result.append({
                            'user_id': record['user_id'],
                            'type': record['type'],
                            'time': record['time']
                        })

                    print("使用備份資料庫查詢成功")
                    return jsonify({
                        'status': 'success',
                        'message': '查詢成功 (使用備份資料庫)',
                        'data': result
                    }), 200
                
                # 備份數據庫查詢...
                # (保留原有的備份數據庫查詢邏輯)
            except Exception as backup_error:
                return jsonify({'status': 'error', 'message': f'查詢失敗: {str(e)}, 備份查詢也失敗: {str(backup_error)}'}), 500
            return jsonify({'status': 'error', 'message': f'查詢失敗: {str(e)}'}), 500
        finally:
            if conn:
                conn.close()

    # 新增的 POST 方法處理，將打卡記錄寫入 Record 表
    elif request.method == 'POST':
        data = request.get_json()
        user_id = data.get('user_id')
        record_type = data.get('type')  # 'i' 或 'o' 表示上班或下班
        record_time = data.get('time')

        # 檢查參數
        if not user_id or not record_type or not record_time:
            return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400

        # check if user_id is valid
        header_user_id = header.get('X-User-ID')
        if header_user_id != user_id:
            return jsonify({'status': 'error', 'message': '無權限訪問'}), 403

        # 檢查打卡類型
        if record_type not in ['i', 'o']:
            return jsonify({'status': 'error', 'message': '打卡類型必須為 i (上班) 或 o (下班)'}), 400

        conn = None  # 初始化 conn 變數
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # 插入打卡記錄到 Record 表
                insert_query = """
                    INSERT INTO Record (user_id, type, time)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(
                    insert_query, (user_id, record_type, record_time))
                conn.commit()

                # 備份到備份數據庫
                try:
                    backup_conn = get_backup_db_connection()
                    with backup_conn.cursor() as backup_cursor:
                        backup_cursor.execute(
                            insert_query, (user_id, record_type, record_time))
                        backup_conn.commit()
                    backup_conn.close()
                    print("備份打卡記錄成功")
                except Exception as backup_error:
                    print(f"備份打卡記錄失敗: {backup_error}")

                return jsonify({
                    'status': 'success',
                    'message': '打卡記錄已新增',
                }), 201

        except Exception as e:
            # 嘗試使用備份數據庫
            try:
                backup_conn = get_backup_db_connection()
                with backup_conn.cursor() as backup_cursor:
                    insert_query = """
                        INSERT INTO Record (user_id, type, time)
                        VALUES (%s, %s, %s)
                    """
                    backup_cursor.execute(
                        insert_query, (user_id, record_type, record_time))
                    backup_conn.commit()
                backup_conn.close()

                return jsonify({
                    'status': 'success',
                    'message': '打卡記錄已新增 (使用備份數據庫)',
                }), 201

            except Exception as backup_error:
                return jsonify({
                    'status': 'error',
                    'message': f'新增打卡記錄失敗: {str(e)}, 備份操作也失敗: {str(backup_error)}'
                }), 500
        finally:
            if conn:
                conn.close()

# finish backup database
# 查詢薪資記錄


@app.route('/employee/salary', methods=['POST'])
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

    try:
        conn = get_db_connection()
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
        conn = get_backup_db_connection()
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
            print("Using Backup Successfully")
            return jsonify({
                'status': 'success',
                'message': '查詢成功',
                'data': result
            }), 200
        return jsonify({'status': 'error', 'message': f'查詢失敗: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/api/login', methods=['POST'])
def login():
    """
    員工登入 API
    需要提供:
    - account: 員工帳號
    - password: 員工密碼
    - role:     身分別
    """
    data = request.get_json()
    account = data.get('account')
    password = data.get('password')
    role = data.get('role')

    if not account or not password or not role:
        return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400

    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # 檢查用戶是否存在
            if role == "employee":
                query = "SELECT * FROM employeeaccount WHERE account = %s AND password = %s"
            elif role == "boss":
                query = "SELECT * FROM bossaccount WHERE account = %s AND password = %s"
            else:
                return jsonify({'status': 'error', 'message': '無效的角色'}), 400

            cursor.execute(query, (account, password))
            user = cursor.fetchone()

            if not user:
                return jsonify({'status': 'error', 'message': '帳號或密碼錯誤'}), 401

            # 生成新的 token
            current_time = time.time()
            new_access_token = hashlib.sha256(
                (account + str(current_time)).encode()).hexdigest()
            new_refresh_token = hashlib.sha256(
                (account + "refresh" + str(current_time)).encode()).hexdigest()

            # 檢查用戶是否已有 token 記錄
            cursor.execute(
                "SELECT * FROM author WHERE user_id = %s", (account,))
            token_record = cursor.fetchone()

            if token_record:
                # 更新現有 token
                update_query = """
                    UPDATE Author 
                    SET access_token = %s, refresh_token = %s, created_at = %s 
                    WHERE user_id = %s
                """
                cursor.execute(update_query, (new_access_token,
                               new_refresh_token, current_time, account))
            else:
                # 創建新的 token 記錄
                insert_query = """
                    INSERT INTO Author (user_id, access_token, refresh_token, created_at)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(
                    insert_query, (account, new_access_token, new_refresh_token, current_time))

            conn.commit()

            # 備份到備份資料庫
            try:
                backup_conn = get_backup_db_connection()
                with backup_conn.cursor() as backup_cursor:
                    if token_record:
                        backup_cursor.execute(
                            update_query, (new_access_token, new_refresh_token, current_time, account))
                    else:
                        backup_cursor.execute(
                            insert_query, (account, new_access_token, new_refresh_token, current_time))
                    backup_conn.commit()
                backup_conn.close()
                print("備份 token 更新成功")
            except Exception as backup_error:
                print(f"備份 token 更新失敗: {backup_error}")

            return jsonify({
                'status': 'success',
                'message': '登入成功',
                'data': {
                    'user_id': account,
                    'role': role,
                    'access_token': new_access_token,
                    'refresh_token': new_refresh_token,
                    'boss_id': user['boss_id'] if role == 'employee' else None
                }
            }), 200

    except Exception as e:
        print(f"登入過程中發生錯誤: {e}")
        try:
            backup_conn = get_backup_db_connection()
            with backup_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                # 檢查用戶是否存在
                if role == "employee":
                    query = "SELECT * FROM employeeaccount WHERE account = %s AND password = %s"
                elif role == "boss":
                    query = "SELECT * FROM bossaccount WHERE account = %s AND password = %s"
                else:
                    return jsonify({'status': 'error', 'message': '無效的角色'}), 400

                cursor.execute(query, (account, password))
                user = cursor.fetchone()

                if not user:
                    return jsonify({'status': 'error', 'message': '帳號或密碼錯誤'}), 401

                # 生成新的 token
                current_time = time.time()
                new_access_token = hashlib.sha256(
                    (account + str(current_time)).encode()).hexdigest()
                new_refresh_token = hashlib.sha256(
                    (account + "refresh" + str(current_time)).encode()).hexdigest()

                # 檢查用戶是否已有 token 記錄
                cursor.execute(
                    "SELECT * FROM author WHERE user_id = %s", (account,))
                token_record = cursor.fetchone()

                if token_record:
                    # 更新現有 token
                    update_query = """
                        UPDATE Author 
                        SET access_token = %s, refresh_token = %s, created_at = %s 
                        WHERE user_id = %s
                    """
                    cursor.execute(update_query, (new_access_token,
                                   new_refresh_token, current_time, account))
                else:
                    # 創建新的 token 記錄
                    insert_query = """
                        INSERT INTO Author (user_id, access_token, refresh_token, created_at)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(
                        insert_query, (account, new_access_token, new_refresh_token, current_time))

                backup_conn.commit()
                conn = backup_conn
                print("使用備份資料庫登入成功")
                return jsonify({
                    'status': 'success',
                    'message': '登入成功',
                    'data': {
                        'user_id': account,
                        'role': role,
                        'access_token': new_access_token,
                        'refresh_token': new_refresh_token,
                        'boss_id': user['boss_id'] if role == 'employee' else None
                    }
                }), 200
        except Exception as backup_e:
            print(f"備份資料庫登入失敗: {backup_e}")
            return jsonify({'status': 'error', 'message': f'登入失敗: {str(e)}，備份資料庫也失敗: {str(backup_e)}'}), 500
        conn.close()


@app.route('/boss/subordinates', methods=['GET'])
@verify_boss_access
def get_boss_subordinates():
    """
    BOSS API：獲取主管的下屬員工列表
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                boss_id = request.headers.get('X-User-ID')

                # 查詢該主管的所有下屬
                cursor.execute("""
                    SELECT account FROM employeeaccount WHERE boss_id = %s
                """, (boss_id,))

                subordinates = [row[0] for row in cursor.fetchall()]

                if not subordinates:
                    return jsonify({'status': 'success', 'data': []}), 200

                return jsonify({'status': 'success', 'data': subordinates}), 200

        except Exception as e:
            return jsonify({'status': 'error', 'message': f'查詢失敗: {str(e)}'}), 500
    except Exception as e:
        print("Exception while connecting to Main YugabyteDB")
        print(e)
        # 使用備用資料庫
        try:
            backup_conn = get_backup_db_connection()
            with backup_conn.cursor() as backup_cursor:
                boss_id = request.headers.get('X-User-ID')

                # 查詢該主管的所有下屬
                backup_cursor.execute("""
                    SELECT account FROM employeeaccount WHERE boss_id = %s
                """, (boss_id,))

                subordinates = [row[0] for row in backup_cursor.fetchall()]

                if not subordinates:
                    return jsonify({'status': 'success', 'data': []}), 200

                return jsonify({'status': 'success', 'data': subordinates}), 200
        except Exception as e:
            print("Exception while connecting to Backup YugabyteDB")
            print(e)
            return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500


# test
if __name__ == "__main__":
    # run the app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
