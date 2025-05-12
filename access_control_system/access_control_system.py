import requests
import paho.mqtt.client as mqtt
import time 


# MQTT 配置
mqtt_broker = "broker.emqx.io"  # MQTT broker
mqtt_port = 1883  

# API 配置
api_url = "http://127.0.0.1:5000/record/" 

#處理異常紀錄
def handle_anomalies(start_time,end_time,start_time_str,end_time_str):
    anomalies,user_to_boss = check_attendance_anomalies(start_time,end_time)
    warning=[]
    worktime = 300      #規定上班時長
    for user_id in user_to_boss:
        times = anomalies.get(user_id)
        if times is None:       #未到
            warning.append({
                "user_id":user_id,
                "type":"absent",
                "duration":worktime,
                "reason":f"{start_time_str} - {end_time_str} : Absent"
            })
        else :
            i_time = times.get("i")
            o_time = times.get("o")
            if o_time is None:    #加班
                duration = end_time-i_time-worktime
                duration_minutes = round(duration / 60, 2)
                warning.append({
                    "user_id":user_id,
                    "type":"overtime",
                    "duration":duration,
                    "reason":f"{start_time_str} - {end_time_str} : overtime {duration/60} minutes"
                })
            else:
                duration = o_time-i_time
                if duration < worktime : #遲到
                    duration = worktime-duration
                    duration_minutes = round(duration / 60, 2)
                    warning.append({
                        "user_id":user_id,
                        "type":"late",
                        "duration":duration,
                        "reason":f"{start_time_str} - {end_time_str} : late {duration_minutes} minutes"
                    })
    send_warning(warning,user_to_boss)

#查詢時間內的打卡紀錄
def check_attendance_anomalies(start_time,end_time):
    payload = {
        "time_start": start_time,
        "time_end":end_time
    }
    response = requests.get(f"{api_url}",json=payload)
    if response.status_code == 200:
        data = response.json()
        anomalies = data.get('data', [])  #打卡紀錄
        user_list = data.get('accounts',[]) #所有employee和對應的boss
    else:
        print(f"Failed to fetch data: {response.text}")
        return {}
    
    user_to_boss = {u['user_id']: u['boss_id'] for u in user_list}
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
    return result,user_to_boss

def send_warning(warning,user_to_boss):
    client = mqtt.Client()
    client.connect(mqtt_broker, mqtt_port)
    for user in warning:
        user_id = user['user_id']
        boss_id = user_to_boss.get(user_id, "Unknown")
        reason = user['reason']
        client.publish(f"warning/{boss_id}/{user_id}",reason,retain=True)  #每個員工都有自己獨立的topic，員工只需要訂閱自己的topic即可，老闆需要訂閱所有人的topic : warning/boss_id/#
        print(f"已發送{user_id}的警告--{reason}")
        timestamp = float(time.time())
        payload = {
            "user_id":user_id,
            "type":user['type'],
            "time":timestamp,
            "duration":user['duration']
        }
        response = requests.post(api_url,json=payload) #把異常紀錄存到DB裡面
        if response.status_code == 201:
            clock_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
            print(f"{clock_time} 已記錄 {user_id} {user['reason']}")
        else:
            print(f"Fail : {response.text}")
    
    client.disconnect()

def main():
    while True:
        start_time_str = input("起始時間(YYYY-MM-DD HH:MM): ")
        end_time_str = input("結束時間(YYYY-MM-DD HH:MM): ")
        start_time = time.strptime(start_time_str,"%Y-%m-%d %H:%M")
        start_time = time.mktime(start_time)
        end_time = time.strptime(end_time_str,"%Y-%m-%d %H:%M")
        end_time = time.mktime(end_time)
        handle_anomalies(start_time,end_time,start_time_str,end_time_str)  # 檢查並處理出勤異常

if __name__ == "__main__":
    main()