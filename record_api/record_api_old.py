from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2, json

app = Flask(__name__)
CORS(app)

# 讀取資料庫設定（單一 url.json）
with open('url.json') as f:
    cfg = json.load(f)

def get_db_connection():
    return psycopg2.connect(
        host=cfg['host'],
        port=cfg['port'],
        dbname=cfg['database'],
        user=cfg['user'],
        password=cfg['password']
    )

@app.route('/record/', methods=['GET', 'POST'])
def record_handler():
    if request.method == 'GET':
        # --- 取資料（原 record_api_1） ---
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
            cur  = conn.cursor()
            cur.execute(
                'SELECT user_id, type, time FROM Record WHERE time >= %s AND time <= %s',
                (ts, te)
            )
            rows = cur.fetchall()
            conn.close()
            data = [
                {'user_id': r[0], 'type': r[1], 'time': r[2]}
                for r in rows
            ]
            return jsonify({'status':'success', 'data': data})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # POST
        # --- 存資料（原 record_api_2） ---
        data = request.get_json() or {}
        uid  = data.get('user_id')
        typ  = data.get('type')
        tm   = data.get('time')

        if uid is None or typ is None or tm is None:
            return jsonify({'error': '請提供 user_id, type, time'}), 400

        try:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute(
                'INSERT INTO Record (user_id, type, time) VALUES (%s, %s, %s)',
                (uid, typ, tm)
            )
            conn.commit()
            conn.close()
            return jsonify({'status':'success'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Flask 伺服器啟動：http://127.0.0.1:5000/")
    app.run(host='0.0.0.0', port=5000, debug=True)
