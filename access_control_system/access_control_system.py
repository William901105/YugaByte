import requests
import paho.mqtt.client as mqtt
import time 

# User清單
employee = ["Jason","Deny","Sally"]

# MQTT 配置
mqtt_broker = "broker.emqx.io"  # MQTT broker
mqtt_port = 1883  

# API 配置
api_url = "http://127.0.0.1:5000/record/" 

# 打卡 呼叫record API(POST)
def clock_in(user_id,type):
    timestamp = float(time.time())  # 取得當前時間的 Unix 時間戳，並轉換為 float
    payload = {  
        "user_id": user_id,
        "type": type,
        "time": timestamp
    }
    response = requests.post(f"{api_url}", json=payload)
    
    if response.status_code == 201:
        clock_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        print(f"打卡成功! User {user_id} {type} at {clock_time}")
    else:
        print(f"打卡失敗! Failed to clock in user {user_id}: {response.text}")

# 查詢出勤異常 呼叫record API(GET)
def check_attendance_anomalies(start_time,end_time):
    payload = {
        "time_start": start_time,
        "time_end":end_time
    }
    response = requests.get(f"{api_url}",json=payload)
    
    if response.status_code == 200:
        data = response.json()
        anomalies = data.get('data', []) #{'data': [{'time': 1746801646.7148416, 'type': 'o', 'user_id': 'Deny'}, {'time': 1746801630.039859, 'type': 'i', 'user_id': 'Jason'}], 'status': 'success'} 只取中間的部分
    else:
        print(f"Failed to fetch data: {response.text}")
        return {}
    
    result = {}
    # 整理一下，留下最早的上班紀錄和最晚的下班記錄
    for record in anomalies:
        user_id = record['user_id']
        r_type = record['type']
        r_time = record['time']

        if user_id not in result:
            result[user_id] = {'i': None, 'o': None}

        if r_type == 'i':
            if result[user_id]['i'] is None or r_time < result[user_id]['i']:
                result[user_id]['i'] = r_time
        elif r_type == 'o':
            if result[user_id]['o'] is None or r_time > result[user_id]['o']:
                result[user_id]['o'] = r_time
    return result

# 透過 MQTT 發送警告
def send_warning_to_mqtt(notice):
    client = mqtt.Client()
    client.connect(mqtt_broker, mqtt_port)
    for user in notice:
        user_id = user['user_id']
        reason = user['reason']
        client.publish(f"warning/{user_id}",reason,retain=True)  #每個員工都有自己獨立的topic，員工只需要訂閱自己的topic即可，老闆需要訂閱所有人的topic : warning/#
        print(f"已發送{user_id}的警告--{reason}")
    
    client.disconnect()

# 處理異常出勤
def handle_anomalies(start_time,end_time,start_time_str,end_time_str):
    anomalies = check_attendance_anomalies(start_time,end_time)
    notice = []
    for user_id in employee:
        times = anomalies.get(user_id)
        if times is None:       #時間區段中沒有任何紀錄
            notice.append({
                "user_id":user_id,
                "reason":f"{start_time_str} - {end_time_str} : Missing clock-in and clock-out records"
            })
        else :
            i_time = times.get("i")
            o_time = times.get("o")
            if i_time is None:      #缺少上班打卡記錄的人
                notice.append({
                    "user_id":user_id,
                    "reason":f"{start_time_str} - {end_time_str} : Missing clock-in record"
                })
            elif o_time is None:    #缺少下班打卡記錄的人
                notice.append({
                    "user_id":user_id,
                    "reason":f"{start_time_str} - {end_time_str} : Missing clock-out record"
                })
            else:
                duration = o_time-i_time
                if duration < 300 : #打卡時間為超過5分鐘就發警告
                    notice.append({
                        "user_id":user_id,
                        "reason":f"{start_time_str} - {end_time_str} : Insufficient attendance duration"
                    })
    send_warning_to_mqtt(notice)

# 主循環，等待用戶輸入選擇
def main():
    while True:
        print("\n選擇操作:")
        print("1. 打卡")
        print("2. 確認出勤異常")
        print("3. 退出")

        choice = input("請輸入選項 (1/2/3): ")

        if choice == '1':
            user_id = str(input("輸入使用者ID: "))
            type = str(input("上班(i) or 下班(o): "))
            clock_in(user_id,type)  # 進行打卡
        elif choice == '2':
            start_time_str = input("起始時間(YYYY-MM-DD HH:MM): ")
            end_time_str = input("結束時間(YYYY-MM-DD HH:MM): ")
            start_time = time.strptime(start_time_str,"%Y-%m-%d %H:%M")
            start_time = time.mktime(start_time)
            end_time = time.strptime(end_time_str,"%Y-%m-%d %H:%M")
            end_time = time.mktime(end_time)
            handle_anomalies(start_time,end_time,start_time_str,end_time_str)  # 檢查並處理出勤異常
        elif choice == '3':
            print("結束")
            break  # 退出程式
        else:
            print("無效選項，請重新輸入。")

# 開始主循環
if __name__ == "__main__":
    main()
