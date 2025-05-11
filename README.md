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















 
