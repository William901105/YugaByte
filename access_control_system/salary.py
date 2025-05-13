import requests
import time
from datetime import datetime, timedelta


def get_base_salary(user_id):
    response = requests.get(f'http://localhost:5000/salary/find', json={
        "user_id": user_id})
    if response.status_code == 200:
        data = response.json()
        return data.get('salary')
    else:
        print(f"查詢 {user_id} 基本薪資失敗 (狀態碼 {response.status_code})")
        exit(1)


def get_logs(start_time, end_time):
    response = requests.get('http://localhost:5000/salary/logs', json={
        "start_time": start_time,
        "end_time": end_time
    })
    logs = response.json()
    if not logs:
        print("沒有發現異常紀錄，無需更新")
    return logs


def update_salary(user_id, type, duration):
    base_salary = get_base_salary(user_id)
    if type == 'late':
        base_salary = base_salary - (10 * duration/60)
    elif type == 'absent':
        base_salary = base_salary - 300
    elif type == 'overtime':
        base_salary = base_salary + (10*1.5*duration/60)

    response = requests.post('http://localhost:5000/salary/update', json={
        "user_id": user_id,
        "salary": base_salary
    })

    if response.status_code == 200:
        print(f"薪資更新成功，使用者 {user_id} 的新薪資為 {base_salary}")
        return response.json()
    else:
        print(f"薪資更新失敗 (狀態碼 {response.status_code})，內容：{response.text}")
        exit(1)


if __name__ == '__main__':
    print("==== 薪資更新系統 ====")
    # run per 10 minutes
    start_time = 1.0
    end_time = time.time()
    while True:
        try:
            logs = get_logs(start_time, end_time)
            """[
                {
                    "duration": 3600.0,
                    "time": 1747117662.1759262,
                    "type": "late",
                    "user_id": "Jason"
                }]"""
            for log in logs:
                res = update_salary(
                    log['user_id'], log['type'], log['duration'])
                print(res)
            # 每10分鐘執行一次
            time.sleep(600)
        except KeyboardInterrupt:
            print("手動中斷，退出系統")
            exit(0)
    """
    start_date_str = input("請輸入起始日期 (YYYY-MM-DD) [Enter預設昨天]: ").strip()
    end_date_str = input("請輸入結束日期 (YYYY-MM-DD) [Enter預設昨天]: ").strip()

    if start_date_str and end_date_str:
        start_time = date_to_timestamp(start_date_str)
        end_time = date_to_timestamp(end_date_str, end_of_day=True)
    else:
        yesterday = datetime.now() - timedelta(days=1)
        start_time = date_to_timestamp(yesterday.strftime("%Y-%m-%d"))
        end_time = date_to_timestamp(
            yesterday.strftime("%Y-%m-%d"), end_of_day=True)

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
    """
