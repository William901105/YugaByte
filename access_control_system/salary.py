import requests
import time
from datetime import datetime, timedelta


def get_base_salary(user_id):
    response = requests.post(f'http://localhost:5000/salary/find', json={
        "user_id": user_id})
    if response.status_code == 200:
        data = response.json()
        return data.get('salary')
    else:
        print(f"查詢 {user_id} 基本薪資失敗 (狀態碼 {response.status_code})")
        exit(1)


def get_logs(start_time, end_time):
    response = requests.post('http://localhost:5000/salary/logs', json={
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
    time.sleep(1)  # 模擬延遲，避免過於頻繁的請求
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
            start_time = end_time
            end_time = end_time + 600
            time.sleep(600)
        except KeyboardInterrupt:
            print("手動中斷，退出系統")
            exit(0)
