import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import time
import uuid

# 讀取 YugabyteDB 的連線設定
with open('url.json') as f:
    data = json.load(f)
    CONFIG = {
        'host': data['host'],
        'port': data['port'],
        'dbName': data['database'],
        'dbUser': data['user'],
        'dbPassword': data['password'],
        'sslMode': '',
        'sslRootCert': ''
    }

# 建立資料庫連線
def connect_db():
    try:
        conn = psycopg2.connect(
            host=CONFIG['host'],
            port=CONFIG['port'],
            database=CONFIG['dbName'],
            user=CONFIG['dbUser'],
            password=CONFIG['dbPassword'],
            connect_timeout=10
        )
        print(">>>> 成功連接 YugabyteDB!")
        return conn
    except Exception as e:
        print("連線資料庫失敗：", e)
        return None

# 初始化 Flask app
app = Flask(__name__)
CORS(app)

# POST /salary/log 新增錯誤紀錄
@app.route('/salary/log', methods=['POST'])
def insert_salary_log():
    data = request.get_json()
    device_id = data.get('device_id')
    timestamp_str = data.get('timestamp')
    error_code = data.get('error_code')
    error_message = data.get('error_message')

    try:
        timestamp = time.mktime(time.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ"))
    except Exception as e:
        return jsonify({"error": "時間格式錯誤"}), 400

    log_id = str(uuid.uuid4())

    conn = connect_db()
    if conn is None:
        return jsonify({"error": "資料庫連線失敗"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO SalaryLog (log_id, device_id, timestamp, error_code, error_message)
            VALUES (%s, %s, %s, %s, %s)
        """, (log_id, device_id, float(timestamp), error_code, error_message))
        conn.commit()
        return jsonify({"result": "success", "log_id": log_id}), 200
    except Exception as e:
        print("新增失敗：", e)
        conn.rollback()
        return jsonify({"error": "新增紀錄失敗"}), 500
    finally:
        cursor.close()
        conn.close()

# GET /salary/logs 查詢錯誤紀錄
@app.route('/salary/logs', methods=['GET'])
def get_salary_logs():
    data = request.get_json()
    device_id = data.get('device_id')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')

    try:
        start_time = time.mktime(time.strptime(start_time_str, "%Y-%m-%dT%H:%M:%SZ"))
        end_time = time.mktime(time.strptime(end_time_str, "%Y-%m-%dT%H:%M:%SZ"))
    except Exception as e:
        return jsonify({"error": "時間格式錯誤"}), 400

    conn = connect_db()
    if conn is None:
        return jsonify({"error": "資料庫連線失敗"}), 500

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cursor.execute("""
            SELECT * FROM SalaryLog
            WHERE device_id = %s AND timestamp BETWEEN %s AND %s
            ORDER BY timestamp ASC
        """, (device_id, float(start_time), float(end_time)))

        rows = cursor.fetchall()
        logs = []
        for row in rows:
            logs.append({
                "log_id": row['log_id'],
                "device_id": row['device_id'],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(row['timestamp'])),
                "error_code": row['error_code'],
                "error_message": row['error_message']
            })
        return jsonify({"logs": logs}), 200
    except Exception as e:
        print("查詢失敗：", e)
        return jsonify({"error": "查詢紀錄失敗"}), 500
    finally:
        cursor.close()
        conn.close()

# POST /salary/add 新增或更新薪資資料
@app.route('/salary/add', methods=['POST'])
def insert_salary():
    data = request.get_json()
    user_id = data.get('user_id')
    salary = data.get('salary')

    if not user_id or salary is None:
        return jsonify({"error": "缺少 user_id 或 salary"}), 400

    conn = connect_db()
    if conn is None:
        return jsonify({"error": "資料庫連線失敗"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO salary (user_id, salary)
            VALUES (%s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET salary = EXCLUDED.salary
        """, (user_id, salary))
        conn.commit()
        return jsonify({"result": "success", "user_id": user_id}), 200
    except Exception as e:
        print("薪資新增失敗：", e)
        conn.rollback()
        return jsonify({"error": "新增薪資失敗"}), 500
    finally:
        cursor.close()
        conn.close()

# 執行 Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
