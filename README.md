# YugaByte Installation
## Enviroment
1. ubuntu 20.04
2. python3
```
sudo apt install python-is-python3
```

3. wget
```
sudo apt install wget
```

## Download Yugabyte
```
wget https://software.yugabyte.com/releases/2.25.0.0/yugabyte-2.25.0.0-b489-linux-x86_64.tar.gz
tar xvfz yugabyte-2.25.0.0-b489-linux-x86_64.tar.gz && cd yugabyte-2.25.0.0/
```

## Configure YugabyteDB
```
./bin/post_install.sh
```


## Create a local cluster
```
./bin/yugabyted start --advertise_address 127.0.0.1
```

## UI
Address: 127.0.0.1:15433

**The address perhaps is 127.0.1.1!!!**

We can use
`./bin/yugabyted status`
to check the correct address.

You can see more information on https://hackmd.io/@WEIHUNGLIN/Bk8-pEnsyl

# Components of Our Project
## access_control_system
	1.透過record_api抓取打卡紀錄，並判斷有無異常
	2.若有異常，將異常傳送給record_api
	3.若有異常，將異常利用MQTT傳送給相對應的employee與boss
## record_api
	1.request一個時間區間，將該時間區間的打卡紀錄response回去
	2.request一筆異常log，將該異常log寫回database
## salary_system
	1.透過salary_api抓取異常log，並處理各項異常log所需要變更的薪資內容
	2.將變更後的薪資內容傳給salary_api
## salary_api
	1.request一個時間區間，將該時間區間的異常log response回去
	2.request一筆薪資內容，將該筆薪資內容寫回database
## employee
	1.需有UI
	2.可以執行註冊/登入
	3.註冊後應將註冊完成的資料傳給employee_api
	4.透過employee_api抓取自己 一段時間區間的打卡紀錄
	5.透過employee_api抓取自己 薪資
	6.可以收到access_control_system所發來的MQTT
## employee_api
	1.request一筆註冊完的帳號資料，將該帳號資料寫回database
	2.request一個user_id與一個時間區間，將該user_id的該時間區間打卡紀錄response回去
	3.request一個user_id，將該user_id的薪資response回去
## boss
	1.需有UI
	2.可以執行登入
	3.透過boss_api抓取自己下屬employee的打卡紀錄
	4.透過boss_api抓取自己下屬employee的薪資
	5.需檢查，不可查別人下屬的資料
## boss_api
	1.request一個user_id與一個時間區間，將該user_id的該時間區間打卡紀錄response回去
	2.request一個user_id，將該user_id的薪資response回去
	3.須注意，要檢查request的user_id是否為其下屬
## authorization_api
	1.request一個access token與user_id，response其是否為合法
	2.request一個refresh token與user_id，response其是否合法，若合法則response更新後的access token與refresh token
	3.更新token後，將新的token更新至database


# Database Table
## authorization(紀錄授權用的token)
	1.user_id : 用戶名稱(boss/employee)
	2.access_token : 授權用的token
	3.refresh_token : access_token過期後，需要換新的token時所用的
	4.created_at : 更新時間
## record(紀錄employee打卡紀錄)
	1.user_id : 用戶名稱(employee)
	2.type : 字串，有兩種(i/o)，分別代表進與出
	3.time : 紀錄的時間
## log(紀錄employee的異常打卡紀錄)
	1.user_id : 用戶名稱(employee)
	2.type : 字串，有三種(absent/late/overtime)，分別代表未到/遲到/加班
	3.time : 異常紀錄的時間
	3.duration : 未到/遲到/加班了多久
## salary(紀錄employee的薪資)
	1.user_id : 用戶名稱(employee)
	2.salary: 薪資
## employee_account(紀錄員工的帳號密碼資訊)
	1.account : 帳號
	2.password : 密碼
	3.boss_id : 所屬的上司
## boss_account(紀錄老闆的帳號密碼)
	1.account : 帳號
	2.password : 密碼

# CLI 使用指南
## cli.py
	1.支援的action：register(註冊)、login(登入)、logout(登出)、status(狀態檢查)、clock(打卡)、records(記錄查詢)、salary(薪資查詢)
	2.基本指令格式：python cli.py [action]
	3.登入資訊儲存於/access_control_system/session.json
	4.注意：cli.py 目前僅用於單元測試，實際使用請參考以下 employeeUI.py 的說明

## employeeUI.py 使用指南
employeeUI.py 是一個整合了命令列功能和互動式界面的員工系統，結合了即時通知功能。

### 啟動方式
```bash
# 進入互動模式（預設）
python .\access_control_system\employeeUI.py


# 使用命令列模式
python .\access_control_system\employeeUI.py [action]
# 其中 [action] 可以是：register、login、logout、status、clock、records、salary、interactive
```

### 互動模式功能
1. **啟動時顯示歡迎選單**
   - 登入系統
   - 註冊新員工
   - 退出程式（隱藏功能）

2. **登入後的主選單**
   - 打卡（上班/下班）
   - 查詢打卡記錄
   - 查詢薪資
   - 查詢登入狀態
   - 查看通知（有新通知時會標記）
   - 登出系統
   - 退出程式（隱藏功能）

3. **特色功能**
   - MQTT 即時通知功能
   - 自動保存登入狀態
   - Token 自動更新機制
   - 支援多種時間格式輸入

### 示範操作
```bash
# 啟動互動模式
python .\access_control_system\employeeUI.py

# 選擇 1 登入系統，輸入帳號密碼
# 例如: Jason / Jason

# 登入成功後，選擇功能編號使用對應功能
# 1: 打卡
# 2: 查詢打卡記錄
# 3: 查詢薪資
# 4: 查詢登入狀態
# 5: 查看通知
# 6: 登出系統
# 0: 退出程式（隱藏功能，與登出的差異在會保留登入資訊，下次打開會跳過登入）
```

### 註意事項
1. 登入資訊儲存於 /access_control_system/employee_session.json
2. 通知功能需要連接網際網路才能正常運作
3. 系統會在後台自動處理 Token 刷新

## cli.py 使用指南 (僅供單元測試使用)
### 示範指令(執行目錄為Yugabyte資料夾時)
```bash
# Jason登入(員工角色)
python .\access_control_system\cli.py login
# 輸入: Jason / Jason / employee

# 執行打卡
python .\access_control_system\cli.py clock

# 查詢記錄與薪資
python .\access_control_system\cli.py records
python .\access_control_system\cli.py salary

# 查看登入狀態
python .\access_control_system\cli.py status

# 登出系統
python .\access_control_system\cli.py logout
```
















 
