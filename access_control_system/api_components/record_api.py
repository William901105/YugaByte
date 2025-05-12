from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import json

app = Flask(__name__)
CORS(app)

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


if __name__ == '__main__':
    print("Flask 伺服器啟動：http://127.0.0.1:5000/")
    app.run(host='0.0.0.0', port=5000, debug=True)
