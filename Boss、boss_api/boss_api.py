import json
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request

app = Flask(__name__)

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

# 員工清單 (從 access_control_system.py 取得)
EMPLOYEES = ["Jason", "Deny", "Sally"]


def get_db_connection():
    """建立與 YugabyteDB 的連線"""
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
        print("成功連接到 YugabyteDB!")
        return conn
    except Exception as e:
        print(f"資料庫連線失敗: {e}")
        return None


@app.route('/api/boss/employees_info', methods=['GET'])
def get_employees_info():
    """
    BOSS API：查詢員工的打卡時間和薪資。
    可以選擇查詢所有員工或特定員工。
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            user_id = request.args.get('user_id')  # 從查詢參數中獲取 user_id

            if user_id:
                # 查詢特定員工
                if user_id not in EMPLOYEES:
                    return jsonify({'status': 'error', 'message': '無效的員工 ID'}), 400
                cursor.execute("""
                    SELECT a.user_id, s.salary
                    FROM Author a
                    JOIN Salary s ON a.user_id = s.user_id
                    WHERE a.user_id = %s
                """, (user_id,))
                employees = cursor.fetchall()

                # 查詢特定員工的打卡紀錄
                clock_records = {}
                cursor.execute("""
                    SELECT r.user_id, r.type, MAX(r.time) as last_time
                    FROM Record r
                    WHERE r.type IN ('i', 'o') AND r.user_id = %s
                    GROUP BY r.user_id, r.type
                """, (user_id,))
                records = cursor.fetchall()
                for record in records:
                    user_id = record['user_id']
                    clock_type = '上班' if record['type'] == 'i' else '下班'
                    if user_id not in clock_records:
                        clock_records[user_id] = {}
                    clock_records[user_id][clock_type] = record['last_time']

                # 整合員工資料、薪資和打卡紀錄
                result = []
                for employee in employees:
                    employee_info = {
                        'user_id': employee['user_id'],
                        'salary': employee['salary'],
                        'clock_records': clock_records.get(employee['user_id'], {})
                    }
                    result.append(employee_info)

                return jsonify({
                    'status': 'success',
                    'message': '查詢成功',
                    'data': result
                }), 200

            else:
                # 查詢所有員工
                cursor.execute("""
                    SELECT a.user_id, s.salary
                    FROM Author a
                    JOIN Salary s ON a.user_id = s.user_id
                    WHERE a.user_id IN %s
                """, (tuple(EMPLOYEES),))  # 使用 IN 子句限制只查詢指定的員工
                employees = cursor.fetchall()

                # 查詢所有員工的打卡紀錄 (簡化版，只取最近一次上班和下班)
                clock_records = {}
                cursor.execute("""
                    SELECT r.user_id, r.type, MAX(r.time) as last_time
                    FROM Record r
                    WHERE r.type IN ('i', 'o') AND r.user_id IN %s
                    GROUP BY r.user_id, r.type
                """, (tuple(EMPLOYEES),))  # 限制只查詢指定的員工
                records = cursor.fetchall()
                for record in records:
                    user_id = record['user_id']
                    clock_type = '上班' if record['type'] == 'i' else '下班'
                    if user_id not in clock_records:
                        clock_records[user_id] = {}
                    clock_records[user_id][clock_type] = record['last_time']

                # 整合員工資料、薪資和打卡紀錄
                result = []
                for employee in employees:
                    employee_info = {
                        'user_id': employee['user_id'],
                        'salary': employee['salary'],
                        'clock_records': clock_records.get(user_id, {})
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
