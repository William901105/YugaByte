import argparse
import requests
import time
import json
import os
from datetime import datetime

BASE_URL = "http://localhost:5000"  # API 的基底 URL
SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session.json")

# 讀取已儲存的登入資訊
def load_session():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"載入登入資訊失敗: {e}")
    return {"access_token": None, "refresh_token": None, "user_id": None}

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

def register_employee():
    """註冊員工"""
    account = input("請輸入帳號: ")
    password = input("請輸入密碼: ")
    boss_id = input("請輸入主管帳號: ")

    try:
        response = requests.post(f"{BASE_URL}/employee/register", json={
            "account": account,
            "password": password,
            "boss_id": boss_id
        })
        
        result = response.json()
        if response.status_code == 200 and result.get("status") == "success":
            print("註冊成功！")
        else:
            print(f"註冊失敗: {result.get('message', '未知錯誤')}")
    except Exception as e:
        print(f"註冊過程中發生錯誤: {e}")

def login():
    """登入"""
    global session  # 明確聲明使用全域變數
    account = input("請輸入帳號: ")
    password = input("請輸入密碼: ")
    role = input("請輸入角色 (預設為 employee(可選boss)，按 Enter 繼續): ") or "employee"

    try:
        response = requests.post(f"{BASE_URL}/api/login", json={
            "account": account,
            "password": password,
            "role": role
        })

        if response.status_code == 200:
            data = response.json()
            # 正確取得巢狀結構中的 token
            if data.get("status") == "success" and data.get("data"):
                session["access_token"] = data["data"]["access_token"]
                session["refresh_token"] = data["data"]["refresh_token"]  # 新增儲存 refresh_token
                session["user_id"] = account
                session["role"] = role  # 儲存角色
                save_session(session)  # 儲存登入資訊
                print("登入成功！")
                print(f"使用者: {account}")
                print(f"角色: {role}")
            else:
                print("登入成功，但無法取得 token")
                print(data)
        else:
            print(f"登入失敗 (HTTP {response.status_code}): {response.json().get('message', '未知錯誤')}")
    except Exception as e:
        print(f"登入過程中發生錯誤: {e}")

def logout():
    """登出"""
    global session
    session = {"access_token": None, "refresh_token": None, "user_id": None, "role": None}
    save_session(session)
    print("已登出系統。")

def refresh_token():
    """刷新 token"""
    if not session["refresh_token"] or not session["user_id"]:
        return False
        
    try:
        response = requests.post(f"{BASE_URL}/authorization/refreshToken", json={
            "refresh_token": session["refresh_token"],
            "user_id": session["user_id"]
        })
        
        if response.status_code == 200:
            data = response.json()
            session["access_token"] = data["new_access_token"]
            session["refresh_token"] = data["new_refresh_token"]
            save_session(session)
            print("Token 已更新")
            return True
        else:
            print("更新 Token 失敗，請重新登入")
            return False
    except Exception as e:
        print(f"刷新 Token 時發生錯誤: {e}")
        return False

def check_login_status():
    """查詢登入狀態"""
    if session["access_token"] and session["user_id"]:
        print(f"目前登入的使用者：{session['user_id']}")
        print(f"角色：{session.get('role', '未知')}")
        
        # 檢查 token 是否有效
        try:
            response = requests.get(f"{BASE_URL}/authorization/authorize", json={
                "access_token": session["access_token"],
                "user_id": session["user_id"]
            })
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result") == "Valid":
                    print("登入狀態：有效")
                elif result.get("result") == "Expired":
                    print("登入狀態：已過期，嘗試刷新...")
                    if refresh_token():
                        print("已自動更新 Token")
                    else:
                        print("刷新失敗，請重新登入")
                else:
                    print(f"登入狀態：無效 ({result.get('result', 'unknown')})")
            else:
                print(f"檢查登入狀態失敗: {response.status_code}")
        except Exception as e:
            print(f"無法連接伺服器，無法驗證登入狀態: {e}")
    else:
        print("尚未登入。")

def clock_in_out():
    """打卡"""
    # 檢查登入狀態
    if not session["access_token"] or not session["user_id"]:
        print("請先登入！")
        return

    # 確保 token 有效
    try:
        response = requests.get(f"{BASE_URL}/authorization/authorize", json={
            "access_token": session["access_token"],
            "user_id": session["user_id"]
        })
        
        if response.status_code != 200 or response.json().get("result") != "Valid":
            if not refresh_token():
                print("認證已過期，請重新登入。")
                return
    except Exception as e:
        print(f"檢查登入狀態時發生錯誤: {e}")
        return

    clock_type = input("請輸入打卡類型 (i: 上班, o: 下班): ")
    if clock_type not in ['i', 'o']:
        print("無效的打卡類型，請輸入 'i' (上班) 或 'o' (下班)")
        return

    current_time = time.time()
    
    try:
        # 設定 HTTP 標頭，包含認證資訊
        headers = {
            "Authorization": session["access_token"],
            "X-User-ID": session["user_id"]
        }
        
        # 改用 /employee/records 端點
        response = requests.post(f"{BASE_URL}/employee/records", 
            json={
                "user_id": session["user_id"],
                "type": clock_type,
                "time": current_time
            },
            headers=headers
        )

        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            if result.get("status") == "success":
                print(result)  # 顯示完整回應，可以用於偵錯
                print(f"打卡成功！")
                print(f"使用者: {session['user_id']}")
                print(f"類型: {'上班' if clock_type == 'i' else '下班'}")
                print(f"時間: {format_timestamp(current_time)}")
            else:
                print(f"打卡失敗: {result.get('message', '未知錯誤')}")
        else:
            print(f"打卡失敗 (HTTP {response.status_code}): {response.json()}")
    except Exception as e:
        print(f"打卡過程中發生錯誤: {e}")

def query_records():
    """查詢打卡記錄"""
    # 檢查登入狀態
    if not session["access_token"] or not session["user_id"]:
        print("請先登入！")
        return

    try:
        # 提供預設值和說明
        print("請輸入時間範圍 (UNIX timestamp)")
        print("可直接按 Enter 查詢今天的記錄")
        
        # 計算今天的開始時間 (00:00:00)
        current_time = time.time()
        today_start = time.strftime("%Y-%m-%d 00:00:00", time.localtime(current_time))
        today_start_timestamp = time.mktime(time.strptime(today_start, "%Y-%m-%d %H:%M:%S"))
        
        # 處理預設值
        start_time_input = input(f"開始時間 (預設: {format_timestamp(today_start_timestamp)}): ")
        start_time = float(start_time_input) if start_time_input else today_start_timestamp
        
        end_time_input = input(f"結束時間 (預設: {format_timestamp(current_time)}): ")
        end_time = float(end_time_input) if end_time_input else current_time
        
        # 設定 HTTP 標頭，包含認證資訊
        headers = {
            "Authorization": session["access_token"],
            "X-User-ID": session["user_id"]
        }
        
        print(f"正在查詢從 {format_timestamp(start_time)} 到 {format_timestamp(end_time)} 的記錄...")
        
        # 直接使用 try-except 來處理可能的錯誤
        try:
            response = requests.get(
                f"{BASE_URL}/employee/records", 
                json={
                    "user_id": session["user_id"],
                    "start_time": start_time,
                    "end_time": end_time
                },
                headers=headers
            )
            
            # 檢查是否是有效的 JSON 回應
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(response.json())
                    # 檢查回應的狀態和資料
                    if result.get("status") == "success" and "data" in result:
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
                        print(f"無法取得打卡記錄: {result.get('message', '未知錯誤')}")
                except ValueError:
                    print(f"伺服器回應的不是有效的 JSON 格式。回應內容: {response.text[:200]}...")
            else:
                print(f"查詢失敗 (HTTP {response.status_code}): {response.text[:200]}...")
        except requests.exceptions.ConnectionError:
            print("無法連接到伺服器，請檢查網路連接或伺服器是否正在運行。")
        except Exception as e:
            print(f"發生未知錯誤: {e}")
            
    except ValueError:
        print("時間格式錯誤，請輸入有效的 UNIX timestamp。")
    except Exception as e:
        print(f"查詢過程中發生錯誤: {e}")

def query_salary():
    """查詢薪資"""
    # 檢查登入狀態
    if not session["access_token"] or not session["user_id"]:
        print("請先登入！")
        return

    # 確保 token 有效
    try:
        # 將 POST 改為 GET
        response = requests.get(f"{BASE_URL}/authorization/authorize", json={
            "access_token": session["access_token"],
            "user_id": session["user_id"]
        })
        
        if response.status_code != 200 or response.json().get("result") != "Valid":
            if not refresh_token():
                print("認證已過期，請重新登入。")
                return
    except Exception as e:
        print(f"檢查登入狀態時發生錯誤: {e}")
        return

    try:
        # 設定 HTTP 標頭，包含認證資訊
        headers = {
            "Authorization": session["access_token"],
            "X-User-ID": session["user_id"]
        }
        
        print(f"正在查詢 {session['user_id']} 的薪資資訊...")
        
        response = requests.post(
            f"{BASE_URL}/employee/salary", 
            json={
                "user_id": session["user_id"]
            },
            headers=headers  # 添加標頭
        )

        print(f"HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("status") == "success" and "data" in result:
                    salary_data = result["data"]
                    print("\n===== 薪資資訊 =====")
                    print(f"員工編號: {session['user_id']}")
                    
                    # 如果資料是列表形式 (可能是多筆記錄)
                    if isinstance(salary_data, list) and len(salary_data) > 0:
                        salary_info = salary_data[0]
                        print(f"薪資: NT$ {salary_info.get('salary', 0):,.2f}")
                    else:
                        # 如果資料是單一物件
                        print(f"薪資: NT$ {salary_data.get('salary', 0):,.2f}")
                else:
                    print(f"無法取得薪資資訊: {result.get('message', '未知錯誤')}")
            except ValueError as json_err:
                print(f"解析 JSON 回應時發生錯誤，回應內容: {response.text}")
        else:
            print(f"查詢失敗 (HTTP {response.status_code}): {response.text}")
    except Exception as e:
        print(f"查詢過程中發生錯誤: {e}")

def main():
    parser = argparse.ArgumentParser(description="Access Control System CLI")
    parser.add_argument("action", choices=["register", "login", "logout", "status", "clock", "records", "salary"], help="選擇要執行的操作")
    args = parser.parse_args()

    if args.action == "register":
        register_employee()
    elif args.action == "login":
        login()
    elif args.action == "logout":
        logout()
    elif args.action == "status":
        check_login_status()
    elif args.action == "clock":
        clock_in_out()
    elif args.action == "records":
        query_records()
    elif args.action == "salary":
        query_salary()

if __name__ == "__main__":
    main()