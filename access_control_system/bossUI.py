import requests
import json
import os
import time
import paho.mqtt.client as mqtt
from datetime import datetime

BASE_URL = "http://localhost:5000"  # API 的基底 URL
SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boss_session.json")
MQTT_BROKER = "broker.emqx.io"  # MQTT broker
MQTT_PORT = 1883
mqtt_client = None
# 存儲警告訊息的列表
warning_messages = []
# 是否有新的未讀通知
has_new_notifications = False

# 讀取已儲存的登入資訊
def load_session():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"載入登入資訊失敗: {e}")
    return {"access_token": None, "refresh_token": None, "user_id": None, "role": None}

# 儲存登入資訊
def save_session(session_data):
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(session_data, f)
    except Exception as e:
        print(f"儲存登入資訊失敗: {e}")

# 初始化 session
session = load_session()

# Unix timestamp 轉換為可讀時間
def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# 可讀時間轉換為 Unix timestamp
def parse_datetime(datetime_str):
    try:
        # 嘗試解析完整的日期時間格式
        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        return dt.timestamp()
    except ValueError:
        try:
            # 嘗試解析只有日期的格式
            dt = datetime.strptime(datetime_str, '%Y-%m-%d')
            return dt.timestamp()
        except ValueError:
            try:
                # 嘗試解析年月日格式
                dt = datetime.strptime(datetime_str, '%Y/%m/%d')
                return dt.timestamp()
            except ValueError:
                try:
                    # 嘗試解析另一種常見格式
                    dt = datetime.strptime(datetime_str, '%d-%m-%Y')
                    return dt.timestamp()
                except ValueError:
                    # 如果無法解析，看是否為數字（已經是 timestamp）
                    if datetime_str.replace('.', '', 1).isdigit():
                        return float(datetime_str)
                    # 如果都不是，返回當前時間
                    print(f"無法識別的時間格式: {datetime_str}，使用當前時間")
                    return time.time()

# MQTT 回調函數 - 連接成功時
def on_connect(client, userdata, flags, reason_code, properties=None):
    # 回調函數中不再輸出連接成功訊息，由 init_mqtt_client 函數處理
    if reason_code != 0:
        print(f"\nMQTT 連接失敗，返回碼: {reason_code}")

# MQTT 回調函數 - 收到消息時
def on_message(client, userdata, msg):
    global warning_messages, has_new_notifications
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        
        # 從主題中提取員工 ID (warning/boss_id/employee_id)
        parts = topic.split('/')
        if len(parts) == 3:
            employee_id = parts[2]
            warning_type = payload
            
            # 將警告類型翻譯為中文
            warning_desc = {
                "absent": "缺勤",
                "overtime": "加班",
                "late": "遲到/早退"
            }.get(warning_type, warning_type)
            
            # 創建警告訊息並添加到列表中
            warning_time = time.time()
            warning_msg = {
                "employee_id": employee_id,
                "type": warning_desc,
                "time": warning_time,
                "formatted_time": format_timestamp(warning_time)
            }
            warning_messages.append(warning_msg)
            
            # 標記有新通知
            has_new_notifications = True
    except Exception as e:
        print(f"\nMQTT 消息處理錯誤: {e}")

# 初始化 MQTT 客戶端
def init_mqtt_client():
    global mqtt_client
    if mqtt_client is None:
        try:
            # 使用較新的 MQTT Client API 版本，避免警告訊息
            mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            mqtt_client.on_connect = on_connect
            mqtt_client.on_message = on_message
            
            print("\n正在連接到 MQTT 服務器...")
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            
            # 使用非阻塞方式啟動網絡循環
            mqtt_client.loop_start()
            
            # 等待連接成功訊息
            wait_count = 0
            while wait_count < 10:  # 最多等待 5 秒
                time.sleep(0.5)
                wait_count += 1
                if session["user_id"] and mqtt_client.is_connected():
                    print(f"\n已成功連接到 MQTT 服務器")
                    # 訂閱該主管所有員工的警告信息
                    topic = f"warning/{session['user_id']}/#"
                    mqtt_client.subscribe(topic)
                    print(f"已訂閱主題: warning/{session['user_id']}/#")
                    break
            
            if wait_count >= 10:
                print("\nMQTT 連接超時，請檢查網絡連接")
                
        except Exception as e:
            print(f"\nMQTT 客戶端初始化失敗: {e}")
            mqtt_client = None

# 停止 MQTT 客戶端
def stop_mqtt_client():
    global mqtt_client
    if mqtt_client:
        try:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            print("\nMQTT 客戶端已斷開連接")
        except Exception as e:
            print(f"\nMQTT 客戶端斷開連接失敗: {e}")
        finally:
            mqtt_client = None

def login():
    """登入"""
    global session
    print("\n===== 主管系統登入 =====")
    account = input("請輸入帳號: ")
    password = input("請輸入密碼: ")
    
    try:
        response = requests.post(f"{BASE_URL}/api/login", json={
            "account": account,
            "password": password,
            "role": "boss"  # 固定為 boss 角色
        })

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and data.get("data"):
                session["access_token"] = data["data"]["access_token"]
                session["refresh_token"] = data["data"]["refresh_token"]
                session["user_id"] = account
                session["role"] = "boss"
                save_session(session)
                print("\n登入成功！")
                print(f"使用者: {account}")
                print(f"角色: boss")
                
                # 登入成功後初始化 MQTT 客戶端並等待連接成功
                init_mqtt_client()
                
                # 暫停一下，確保 MQTT 相關訊息顯示完畢
                time.sleep(1)
                
                return True
            else:
                print(f"\n登入失敗: {data.get('message', '未知錯誤')}")
                return False
        else:
            print(f"\n登入失敗 (HTTP {response.status_code}): {response.json().get('message', '未知錯誤')}")
            return False
    except Exception as e:
        print(f"\n登入過程中發生錯誤: {e}")
        return False

def refresh_token():
    """刷新 token"""
    if not session["refresh_token"] or not session["user_id"]:
        return False
        
    try:
        # 使用 JSON 請求體發送刷新請求
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{BASE_URL}/authorization/refreshToken", 
            json={
                "refresh_token": session["refresh_token"],
                "user_id": session["user_id"]
            },
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            session["access_token"] = data["new_access_token"]
            session["refresh_token"] = data["new_refresh_token"]
            save_session(session)
            return True
        else:
            print("更新 Token 失敗，請重新登入")
            return False
    except Exception as e:
        print(f"刷新 Token 時發生錯誤: {e}")
        return False

def check_auth():
    """檢查認證狀態"""
    if not session["access_token"] or not session["user_id"]:
        print("\n您尚未登入，請先登入系統。")
        return False

    try:
        # 使用 JSON 請求體發送認證請求
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{BASE_URL}/authorization/authorize", 
            json={
                "access_token": session["access_token"],
                "user_id": session["user_id"]
            },
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("result") == "Valid":
                return True
            elif result.get("result") == "Expired":
                print("\nToken 已過期，嘗試刷新...")
                if refresh_token():
                    print("已自動更新 Token")
                    return True
                else:
                    print("刷新失敗，請重新登入")
                    return False
            else:
                print(f"\n認證無效: {result.get('result', 'unknown')}")
                return False
        else:
            print(f"\n檢查認證狀態失敗: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"\n檢查認證狀態時發生錯誤: {e}")
        return False

def get_subordinates():
    """獲取下屬清單"""
    if not session["access_token"] or not session["user_id"]:
        print("\n您尚未登入，請先登入系統。")
        return []

    try:
        # 使用 HTTP 頭部發送認證信息
        headers = {
            "Authorization": session["access_token"],
            "X-User-ID": session["user_id"]
        }
        
        response = requests.get(f"{BASE_URL}/boss/subordinates", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success" and "data" in result:
                subordinates = result["data"]
                return subordinates
            else:
                print(f"\n獲取下屬清單失敗: {result.get('message', '未知錯誤')}")
                return []
        else:
            print(f"\n獲取下屬清單失敗 (HTTP {response.status_code})")
            return []
    except Exception as e:
        print(f"\n獲取下屬清單時發生錯誤: {e}")
        return []

def query_employee_records():
    """查詢員工打卡記錄"""
    if not check_auth():
        print("\n認證失敗，請重新登入。")
        return
    
    # 獲取下屬清單
    subordinates = get_subordinates()
    if not subordinates:
        print("\n您沒有下屬或無法獲取下屬清單。")
        return
    
    print("\n===== 查詢員工打卡記錄 =====")
    
    # 顯示下屬列表
    print("\n您的下屬清單:")
    for i, emp in enumerate(subordinates, 1):
        print(f"{i}. {emp}")
    
    # 選擇要查詢的員工
    while True:
        emp_idx = input("\n請選擇要查詢的員工編號 (輸入 0 返回): ")
        if emp_idx == "0":
            return
        
        try:
            emp_idx = int(emp_idx) - 1
            if 0 <= emp_idx < len(subordinates):
                employee_id = subordinates[emp_idx]
                break
            else:
                print("無效的選擇，請重新輸入。")
        except ValueError:
            print("請輸入有效的數字。")
    
    # 設定時間範圍
    print("\n請輸入時間範圍")
    print("格式: YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD")
    print("例如: 2025-05-24 00:00:00 或 2025-05-24")
    print("可直接按 Enter 查詢今天的記錄")
    
    # 計算今天的開始時間 (00:00:00)
    current_time = time.time()
    today_start = time.strftime("%Y-%m-%d 00:00:00", time.localtime(current_time))
    today_start_timestamp = time.mktime(time.strptime(today_start, "%Y-%m-%d %H:%M:%S"))
    
    # 處理預設值和用戶輸入
    start_time_input = input(f"開始時間 (預設: {today_start}): ")
    start_time = parse_datetime(start_time_input) if start_time_input else today_start_timestamp
    
    end_time_input = input(f"結束時間 (預設: {format_timestamp(current_time)}): ")
    end_time = parse_datetime(end_time_input) if end_time_input else current_time
    
    try:
        # 設定 HTTP 標頭，包含認證資訊
        headers = {
            "Authorization": session["access_token"],
            "X-User-ID": session["user_id"],
            "Content-Type": "application/json"
        }
        
        # 提示訊息顯示人類可讀的時間格式
        print(f"\n正在查詢 {employee_id} 從 {format_timestamp(start_time)} 到 {format_timestamp(end_time)} 的記錄...")
        
        # 發送請求
        response = requests.post(
            f"{BASE_URL}/boss/subordinate_record", 
            json={
                "user_id": employee_id,
                "start_time": start_time,
                "end_time": end_time
            },
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            # 檢查回應格式是否符合預期
            if "data" in result:
                records = result["data"]
                print("\n===== 打卡記錄 =====")
                if not records:
                    print("該時間範圍內沒有打卡記錄。")
                else:
                    # 按時間排序，最新的在前
                    records.sort(key=lambda x: x["time"], reverse=True)
                    for i, record in enumerate(records, 1):
                        record_time = format_timestamp(record["time"])
                        record_type = "上班" if record["type"] == "i" else "下班"
                        print(f"{i}. {record_time} - {record_type}")
            else:
                print(f"\n無法取得打卡記錄: {result.get('message', '未知錯誤')}")
        else:
            print(f"\n查詢失敗 (HTTP {response.status_code})")
    except Exception as e:
        print(f"\n查詢過程中發生錯誤: {e}")
    
    input("\n按 Enter 返回主選單...")

def query_employee_salary():
    """查詢員工薪資"""
    if not check_auth():
        print("\n認證失敗，請重新登入。")
        return
    
    # 獲取下屬清單
    subordinates = get_subordinates()
    if not subordinates:
        print("\n您沒有下屬或無法獲取下屬清單。")
        return
    
    print("\n===== 查詢員工薪資 =====")
    
    # 顯示下屬列表
    print("\n您的下屬清單:")
    for i, emp in enumerate(subordinates, 1):
        print(f"{i}. {emp}")
    
    # 選擇要查詢的員工
    while True:
        emp_idx = input("\n請選擇要查詢的員工編號 (輸入 0 返回): ")
        if emp_idx == "0":
            return
        
        try:
            emp_idx = int(emp_idx) - 1
            if 0 <= emp_idx < len(subordinates):
                employee_id = subordinates[emp_idx]
                break
            else:
                print("無效的選擇，請重新輸入。")
        except ValueError:
            print("請輸入有效的數字。")
    
    try:
        # 設定 HTTP 標頭，包含認證資訊
        headers = {
            "Authorization": session["access_token"],
            "X-User-ID": session["user_id"],
            "Content-Type": "application/json"
        }
        
        # 顯示正在查詢的提示訊息
        print(f"\n正在查詢 {employee_id} 的薪資資訊...")
        
        # 發送請求
        response = requests.post(
            f"{BASE_URL}/boss/subordinate_salary", 
            json={
                "user_id": employee_id
            },
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            # 檢查回應格式是否符合預期
            if "data" in result:
                salary_data = result["data"]
                print("\n===== 薪資資訊 =====")
                print(f"員工編號: {employee_id}")
                
                # 如果資料是列表形式 (可能是多筆記錄)
                if isinstance(salary_data, list) and len(salary_data) > 0:
                    salary_info = salary_data[0]
                    print(f"薪資: NT$ {salary_info.get('salary', 0):,.2f}")
                else:
                    # 如果資料是單一物件
                    print(f"薪資: NT$ {salary_data.get('salary', 0):,.2f}")
            else:
                print(f"\n無法取得薪資資訊: {result.get('message', '未知錯誤')}")
        else:
            print(f"\n查詢失敗 (HTTP {response.status_code})")
    except Exception as e:
        print(f"\n查詢過程中發生錯誤: {e}")
    
    input("\n按 Enter 返回主選單...")

def logout():
    """登出系統"""
    global session
    
    # 登出前停止 MQTT 客戶端
    stop_mqtt_client()
    
    session = {"access_token": None, "refresh_token": None, "user_id": None, "role": None}
    save_session(session)
    print("\n已登出系統。")

def show_menu():
    """顯示主選單"""
    # 如果有新通知，先顯示通知提示
    check_notifications()
    
    print("\n===== 主管系統選單 =====")
    print("1. 查詢員工打卡記錄")
    print("2. 查詢員工薪資")
    print("3. 查看即時警告通知")
    
    # 如果有未讀通知，在選項 3 旁邊標記 (*)
    if has_new_notifications:
        print("   * 有新的警告通知！")
    
    print("4. 登出系統")
    print("0. 退出程式")

# 檢查並顯示通知提示
def check_notifications():
    global has_new_notifications
    
    if has_new_notifications:
        print("\n【您有新的警告通知！請選擇功能 3 查看詳情。】")
        has_new_notifications = False  # 顯示提示後重置標記

def view_warnings():
    """查看目前的警告通知"""
    global warning_messages, has_new_notifications
    
    if not check_auth():
        print("\n認證失敗，請重新登入。")
        return
        
    print("\n===== 即時警告通知 =====")
    
    if not warning_messages:
        print("目前沒有任何警告通知。")
    else:
        print(f"共有 {len(warning_messages)} 條警告通知：\n")
        
        # 按時間排序，最新的在前面
        sorted_warnings = sorted(warning_messages, key=lambda x: x["time"], reverse=True)
        
        for i, warning in enumerate(sorted_warnings, 1):
            print(f"{i}. 員工 ID: {warning['employee_id']}")
            print(f"   警告類型: {warning['type']}")
            print(f"   時間: {warning['formatted_time']}")
            print(f"   {'-' * 30}")
    
    # 提供清除警告的選項
    if warning_messages:
        choice = input("\n輸入 'c' 清除所有警告，或按 Enter 返回主選單: ")
        if choice.lower() == 'c':
            warning_messages.clear()
            print("已清除所有警告通知。")
    else:
        input("\n按 Enter 返回主選單...")
    
    # 重置新通知標記
    has_new_notifications = False

def main():
    """主程式"""
    print("\n歡迎使用主管系統")
    
    # 檢查是否已經登入
    if not session["access_token"] or not session["user_id"] or not check_auth():
        if not login():
            print("\n登入失敗，程式結束。")
            return
    else:
        # 如果已經登入，初始化 MQTT 客戶端
        init_mqtt_client()
    
    try:
        while True:
            # 顯示選單（包含檢查通知）
            show_menu()
            choice = input("\n請選擇功能 (0-4): ")
            
            if choice == "1":
                query_employee_records()
            elif choice == "2":
                query_employee_salary()
            elif choice == "3":
                view_warnings()
            elif choice == "4":
                logout()
                print("\n請重新登入以繼續使用系統。")
                if not login():
                    print("\n登入失敗，程式結束。")
                    break
            elif choice == "0":
                # 退出前停止 MQTT 客戶端
                stop_mqtt_client()
                print("\n感謝使用主管系統，再見！")
                break
            else:
                print("\n無效的選擇，請重新輸入。")
    except KeyboardInterrupt:
        # 處理 Ctrl+C 中斷
        stop_mqtt_client()
        print("\n程式已中斷，感謝使用主管系統！")
    except Exception as e:
        # 處理其他例外
        stop_mqtt_client()
        print(f"\n程式發生錯誤: {e}")
        print("程式已終止。")

if __name__ == "__main__":
    main() 