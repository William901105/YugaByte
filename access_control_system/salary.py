import requests
import time
from datetime import datetime, timedelta

def get_base_salary(user_id):
    response = requests.get(f'http://localhost:5000/salary/{user_id}')
    if response.status_code == 200:
        data = response.json()
        return data.get('salary', 0)
    else:
        print(f"查詢 {user_id} 基本薪資失敗 (狀態碼 {response.status_code})")
        exit(1)

def get_logs(start_time, end_time):
    response = requests.get('http://localhost:5000/salary/logs', json={
        "start_time": start_time,
        "end_time": end_time
    })
    logs = response.json().get("logs", [])
    if not logs:
        print("沒有發現異常紀錄，無需更新")
    return logs

def update_salary(user_id, base_salary, logs):
    late_penalty = sum(log['duration'] / 60 * 1 for log in logs if log['error_code'] == 'E101')
    absent_penalty = 1200 if any(log['error_code'] == 'E102' for log in logs) else 0
    overtime_bonus = sum(log['duration'] / 3600 * 200 for log in logs if log['error_code'] == 'E103')

    final_salary = base_salary + overtime_bonus - late_penalty - absent_penalty
    response = requests.post('http://localhost:5000/salary', json={
        "user_id": user_id,
        "salary": final_salary
    })

    if response.status_code == 200:
        return response.json()
    else:
        print(f"薪資更新失敗 (狀態碼 {response.status_code})，內容：{response.text}")
        exit(1)

def date_to_timestamp(date_str, end_of_day=False):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    if end_of_day:
        dt = dt + timedelta(hours=23, minutes=59, seconds=59)
    return int(time.mktime(dt.timetuple()))

if __name__ == '__main__':
    start_date_str = input("請輸入起始日期 (YYYY-MM-DD) [Enter預設昨天]: ").strip()
    end_date_str = input("請輸入結束日期 (YYYY-MM-DD) [Enter預設昨天]: ").strip()

    if start_date_str and end_date_str:
        start_time = date_to_timestamp(start_date_str)
        end_time = date_to_timestamp(end_date_str, end_of_day=True)
    else:
        yesterday = datetime.now() - timedelta(days=1)
        start_time = date_to_timestamp(yesterday.strftime("%Y-%m-%d"))
        end_time = date_to_timestamp(yesterday.strftime("%Y-%m-%d"), end_of_day=True)

    print(f"分析時間區間: {start_time} ~ {end_time} (含結束日整天)")
    logs = get_logs(start_time, end_time)

    processed_users = set()
    for log in logs:
        user_id = log['user_id']
        if user_id not in processed_users:
            user_logs = [l for l in logs if l['user_id'] == user_id]
            base_salary = get_base_salary(user_id)
            result = update_salary(user_id, base_salary, user_logs)
            print(f"已更新 {user_id} 薪資結果: {result}")
            processed_users.add(user_id)
