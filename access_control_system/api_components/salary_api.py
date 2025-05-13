import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from datetime import datetime

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


# 初始化 Flask app
app = Flask(__name__)
CORS(app)


# API 端點


@app.route('/salary/logs', methods=['GET'])  # 查詢日誌
def get_salary_logs():
    # get query parameters from request
    data = request.get_json()
    start_time = data.get('start')
    end_time = data.get('end')

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


@app.route('/salary', methods=['POST'])  # 新增或更新薪資
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
        print("haha")
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
