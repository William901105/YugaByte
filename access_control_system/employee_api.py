import json
import time
import hashlib
import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify

app = Flask(__name__)

# 讀取資料庫連線設定
with open('access_control_system/url.json') as f:
    data = json.load(f)
    HOST = data['host']
    PORT = data['port']

# 資料庫連線設定
CONFIG = {
    'host': HOST,
    'port': PORT,
    'dbName': 'yugabyte',
    'dbUser': 'yugabyte',
    'dbPassword': 'yugabyte',
    'sslMode': '',
    'sslRootCert': ''
}

print(f"資料庫連線設定: 主機={HOST}, 埠號={PORT}")

def get_db_connection():
    """建立與資料庫的連線"""
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

# 員工註冊
@app.route('/api/register', methods=['POST'])
def register():
    """
    員工註冊
    需要提供 user_id (員工ID)
    """
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400
    
    # 產生token
    access_token = hashlib.sha256(str(user_id).encode()).hexdigest()
    refresh_token = hashlib.sha256(str(user_id + "refresh").encode()).hexdigest()
    created_at = time.time()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500
    
    try:
        with conn.cursor() as cursor:
            # 檢查用戶是否已存在
            check_query = "SELECT user_id FROM Author WHERE user_id = %s"
            cursor.execute(check_query, (user_id,))
            if cursor.fetchone():
                return jsonify({'status': 'error', 'message': '用戶已存在'}), 409
            
            # 新增用戶
            insert_query = """
                INSERT INTO Author (user_id, access_token, refresh_token, created_at)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (user_id, access_token, refresh_token, created_at))
            conn.commit()
            
            return jsonify({
                'status': 'success',
                'message': '註冊成功',
                'data': {
                    'user_id': user_id,
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
            }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': f'註冊失敗: {str(e)}'}), 500
    finally:
        conn.close()

# 員工登入
@app.route('/api/login', methods=['POST'])
def login():
    """
    員工登入
    需要提供 user_id (員工ID)
    """
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            # 檢查用戶是否存在
            query = "SELECT user_id, access_token, refresh_token FROM Author WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({'status': 'error', 'message': '用戶不存在'}), 404
            
            # 更新token
            access_token = hashlib.sha256(str(user_id + str(time.time())).encode()).hexdigest()
            refresh_token = hashlib.sha256(str(user_id + "refresh" + str(time.time())).encode()).hexdigest()
            created_at = time.time()
            
            update_query = """
                UPDATE Author 
                SET access_token = %s, refresh_token = %s, created_at = %s
                WHERE user_id = %s
            """
            cursor.execute(update_query, (access_token, refresh_token, created_at, user_id))
            conn.commit()
            
            return jsonify({
                'status': 'success',
                'message': '登入成功',
                'data': {
                    'user_id': user_id,
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
            }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': f'登入失敗: {str(e)}'}), 500
    finally:
        conn.close()

# 驗證token
def verify_token(user_id, access_token):
    """驗證用戶token"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            query = "SELECT access_token, created_at FROM Author WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
                
            stored_token, created_at = result
            
            # token是否匹配以及是否在有效期內 (假設token有效期為24小時)
            is_valid = (stored_token == access_token) and (time.time() - created_at < 86400)
            return is_valid
    except Exception as e:
        print(f"驗證token失敗: {e}")
        return False
    finally:
        conn.close()

# 員工打卡 (上班/下班)
@app.route('/api/clock', methods=['POST'])
def clock():
    """
    員工打卡
    需要提供 user_id (員工ID), access_token (訪問token), type (打卡類型: 'i' 上班, 'o' 下班)
    """
    data = request.get_json()
    user_id = data.get('user_id')
    access_token = data.get('access_token')
    clock_type = data.get('type')
    
    if not all([user_id, access_token, clock_type]) or clock_type not in ['i', 'o']:
        return jsonify({'status': 'error', 'message': '缺少必要參數或參數無效'}), 400
    
    # 驗證token
    if not verify_token(user_id, access_token):
        return jsonify({'status': 'error', 'message': '無效的token或token已過期'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500
    
    try:
        with conn.cursor() as cursor:
            # 記錄打卡
            current_time = time.time()
            insert_query = "INSERT INTO Record (user_id, type, time) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (user_id, clock_type, current_time))
            conn.commit()
            
            return jsonify({
                'status': 'success',
                'message': '打卡成功',
                'data': {
                    'user_id': user_id,
                    'type': '上班' if clock_type == 'i' else '下班',
                    'time': current_time
                }
            }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': f'打卡失敗: {str(e)}'}), 500
    finally:
        conn.close()



# 查詢打卡記錄
@app.route('/api/records', methods=['GET'])
def get_records():
    """
    查詢打卡記錄
    需要提供 user_id (員工ID), access_token (訪問token)
    可選參數: start_time, end_time (查詢範圍)
    """
    user_id = request.args.get('user_id')
    access_token = request.args.get('access_token')
    start_time = request.args.get('start_time', type=float, default=0)
    end_time = request.args.get('end_time', type=float, default=time.time())
    
    if not all([user_id, access_token]):
        return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400
    
    # 驗證token
    if not verify_token(user_id, access_token):
        return jsonify({'status': 'error', 'message': '無效的token或token已過期'}), 401
    
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
            cursor.execute(query, (user_id, start_time, end_time))
            records = cursor.fetchall()
            
            result = []
            for record in records:
                result.append({
                    'user_id': record['user_id'],
                    'type': '上班' if record['type'] == 'i' else '下班',
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



# 查詢薪資
@app.route('/api/salary', methods=['GET'])
def get_salary():
    """
    查詢基本薪資
    需要提供 user_id (員工ID), access_token (訪問token)
    """
    user_id = request.args.get('user_id')
    access_token = request.args.get('access_token')
    
    if not all([user_id, access_token]):
        return jsonify({'status': 'error', 'message': '缺少必要參數'}), 400
    
    # 驗證token
    if not verify_token(user_id, access_token):
        return jsonify({'status': 'error', 'message': '無效的token或token已過期'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500
    
    try:
        with conn.cursor() as cursor:
            # 獲取基本薪資
            query = "SELECT salary FROM Salary WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'status': 'error', 'message': '未找到薪資信息'}), 404
                
            base_salary = result[0]
            
            return jsonify({
                'status': 'success',
                'message': '查詢成功',
                'data': {
                    'user_id': user_id,
                    'base_salary': base_salary
                }
            }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'查詢失敗: {str(e)}'}), 500
    finally:
        conn.close()

# 檢查健康狀態
@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': '資料庫連線失敗'}), 500
    
    try:
        with conn.cursor() as cursor:
            # 簡單查詢驗證資料庫是否正常運行
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return jsonify({'status': 'success', 'message': '系統正常運行中'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'健康檢查失敗: {str(e)}'}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)