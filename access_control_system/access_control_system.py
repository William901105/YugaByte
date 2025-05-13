import requests
import paho.mqtt.client as mqtt
import time


# MQTT 配置
mqtt_broker = "broker.emqx.io"  # MQTT broker
mqtt_port = 1883

# API 配置
api_url = "http://127.0.0.1:5000/record"

# 處理異常紀錄


def handle_anomalies(start_time, end_time):
    anomalies, user_to_boss = check_attendance_anomalies(start_time, end_time)
    warning = []
    worktime = 300  # 規定上班時長
    for u in user_to_boss:
        user_id = u['employee']
        times = anomalies.get(user_id)
        if times is None:  # 未到
            warning.append({
                "user_id": user_id,
                "type": "absent",
                "duration": worktime,
                "time": start_time
            })
        else:
            i_time = times.get("i")
            o_time = times.get("o")
            if o_time is None:  # 加班(未下班), 強迫下班
                duration = end_time-i_time-worktime
                warning.append({
                    "user_id": user_id,
                    "type": "overtime",
                    "duration": duration,
                    "time": start_time
                })
            else:
                duration = o_time-i_time
                if duration < worktime:  # 遲到/早退
                    duration = worktime-duration
                    warning.append({
                        "user_id": user_id,
                        "type": "late",
                        "duration": duration,
                        "time": start_time
                    })
    send_warning(warning, user_to_boss)

# 查詢時間內的打卡紀錄


def check_attendance_anomalies(start_time, end_time):
    payload = {
        "time_start": start_time,
        "time_end": end_time
    }
    response = requests.get(f"{api_url}", json=payload)
    if response.status_code == 200:
        data = response.json()
        anomalies = data.get('data', [])  # 打卡紀錄
        user_list = data.get('accounts', [])  # 所有employee和對應的boss
    else:
        print(f"Failed to fetch data: {response.text}")
        return {}

    user_to_boss = user_list
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
    return result, user_to_boss


def send_warning(warning, user_to_boss):
    client = mqtt.Client()
    client.connect(mqtt_broker, mqtt_port)
    for user in warning:
        user_id = user['user_id']
        # find the boss id
        for u in user_to_boss:
            if u['employee'] == user_id:
                boss_id = u['boss']
                break
        reason = user['type']
        # 每個員工都有自己獨立的topic，員工只需要訂閱自己的topic即可，老闆需要訂閱所有人的topic : warning/boss_id/#
        client.publish(f"warning/{boss_id}/{user_id}", reason, retain=True)
        print(f"已發送{user_id}的警告--{reason}")
        timestamp = time.time()
        payload = {
            "user_id": user_id,
            "type": user['type'],
            "time": timestamp,
            "duration": user['duration']
        }
        response = requests.post(api_url, json=payload)  # 把異常紀錄存到DB裡面
        if response.status_code == 201:
            print(f"已記錄 {user_id} {user['type']} 的異常紀錄")
        else:
            print(f"Fail : {response.text}")

    client.disconnect()


def main():
    start_time = 1
    end_time = time.time()
    # update the log every day
    while True:
        handle_anomalies(start_time, end_time)  # 檢查並處理出勤異常
        start_time = end_time
        end_time = end_time + 86400
        time.sleep(86400)  # 每天檢查一次


if __name__ == "__main__":
    main()
