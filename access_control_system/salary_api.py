# modifier: 113791012
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import time
import uuid
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

# 初始化 Flask app
app = Flask(__name__)
CORS(app)


def get_connection():
    return psycopg2.connect(
        host=CONFIG['host'],
        port=CONFIG['port'],
        database=CONFIG['dbName'],
        user=CONFIG['dbUser'],
        password=CONFIG['dbPassword'],
        sslrootcert=CONFIG['sslRootCert'])

# API 端點


@app.route('/salary/logs', methods=['GET'])
def get_salary_logs():
    start_time = request.args.get('start')
    end_time = request.args.get('end')


@app.route('/salary/<user_id>', methods=['GET'])
def get_salary(user_id):
    """查詢單一用戶薪資"""
    if not user_id or not user_id.strip():
        return jsonify({"error": "Invalid user_id"}), 400

    try:
        conn = DBConnection.get_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("""
                SELECT user_id, salary, 
                       to_char(update_time, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as update_time
                FROM salary
                WHERE user_id = %s
            """, (user_id,))

            if row := cursor.fetchone():
                return jsonify(dict(row))
            return jsonify({"error": "User not found"}), 404

    except Exception as e:
        app.logger.error(f"Salary query failed: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    finally:
        if conn:
            conn.close()


@app.route('/salary', methods=['POST', 'PUT'])
def update_salary():
    """更新薪資 (支援 POST/PUT)"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    user_id = data.get('user_id')
    salary = data.get('salary')

    # 驗證輸入
    if not user_id or not isinstance(salary, (int, float)):
        return jsonify({"error": "Invalid user_id or salary"}), 400

    try:
        conn = DBConnection.get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO salary (user_id, salary)
                VALUES (%s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET salary = EXCLUDED.salary,
                              update_time = CURRENT_TIMESTAMP
                RETURNING user_id, salary
            """, (user_id, salary))

            conn.commit()
            updated_row = cursor.fetchone()
            return jsonify({
                "user_id": updated_row[0],
                "salary": updated_row[1],
                # 回傳更新後資料與狀態（created or updated）
                "status": "updated" if cursor.rowcount > 1 else "created"
            })

    except Exception as e:
        conn.rollback()
        app.logger.error(f"Update failed: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    finally:
        if conn:
            conn.close()


@app.route('/salary/log', methods=['POST'])
def add_error_log():
    """新增異常日誌"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    required_fields = ['user_id', 'error_code', 'error_message']
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400

    log_data = {
        'log_id': str(uuid.uuid4()),
        'user_id': data['user_id'],
        'timestamp': time.time(),  # 自動記錄當前時間
        'error_code': data['error_code'],
        'error_message': data['error_message'],
        'duration': float(data.get('duration', 0))
    }

    try:
        conn = DBConnection.get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO SalaryLog 
                (log_id, user_id, timestamp, error_code, error_message, duration)
                VALUES (%(log_id)s, %(user_id)s, %(timestamp)s, 
                       %(error_code)s, %(error_message)s, %(duration)s)
            """, log_data)

            conn.commit()
            return jsonify({"log_id": log_data['log_id']}), 201

    except Exception as e:
        conn.rollback()
        app.logger.error(f"Log insert failed: {str(e)}")
        return jsonify({"error": "Database error"}), 500
    finally:
        if conn:
            conn.close()

# 健康檢查端點


@app.route('/health', methods=['GET'])
def health_check():
    try:
        conn = DBConnection.get_connection()
        conn.cursor().execute("SELECT 1")
        return jsonify({"status": "healthy"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
