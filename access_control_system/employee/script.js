/**
 * 員工管理系統前端腳本
 * 實現所有功能，包括身份驗證、打卡、記錄查詢和薪資查詢
 */

// 全局變數
const BASE_URL = "http://localhost:5000";
const SESSION_KEY = "employee_system_session";

// API Logger - 用於記錄所有API請求和回應
const apiLogger = {
    // 記錄API請求
    logRequest: function(method, url, headers, body) {
        console.group(`%c🚀 API請求: ${method} ${url}`, 'color: #4CAF50; font-weight: bold;');
        console.log('時間:', new Date().toLocaleString('zh-TW'));
        console.log('方法:', method);
        console.log('URL:', url);
        console.log('標頭:', headers || '無');
        console.log('內容:', body || '無');
        console.groupEnd();
    },
    
    // 記錄API回應
    logResponse: function(method, url, status, statusText, data) {
        const isSuccess = status >= 200 && status < 300;
        const style = isSuccess 
            ? 'color: #2196F3; font-weight: bold;'
            : 'color: #F44336; font-weight: bold;';
        
        console.group(`%c📡 API回應: ${method} ${url} - ${status} ${statusText}`, style);
        console.log('時間:', new Date().toLocaleString('zh-TW'));
        console.log('狀態:', status, statusText);
        console.log('資料:', data || '無');
        console.groupEnd();
    },
    
    // 記錄API錯誤
    logError: function(method, url, error) {
        console.group(`%c❌ API錯誤: ${method} ${url}`, 'color: #F44336; font-weight: bold;');
        console.log('時間:', new Date().toLocaleString('zh-TW'));
        console.log('錯誤:', error.message);
        console.log('堆疊:', error.stack);
        console.groupEnd();
    }
};

// 封裝XMLHttpRequest函數以加入日誌功能並支持GET請求帶body
function loggedXHR(url, options = {}) {
    return new Promise((resolve, reject) => {
        const method = options.method || 'GET';
        const headers = options.headers || {};
        const body = options.body || null;
        const bodyObj = body ? JSON.parse(body) : null;
        
        // 記錄請求
        apiLogger.logRequest(method, url, headers, bodyObj);
        
        // 創建XMLHttpRequest對象
        const xhr = new XMLHttpRequest();
        xhr.open(method, url, true);
        
        // 設置請求頭
        xhr.setRequestHeader('Content-Type', 'application/json');
        for (const [key, value] of Object.entries(headers)) {
            xhr.setRequestHeader(key, value);
        }
        
        // 處理回應
        xhr.onload = function() {
            let responseData;
            try {
                responseData = JSON.parse(xhr.responseText);
            } catch (error) {
                responseData = xhr.responseText;
            }
            
            // 記錄回應
            apiLogger.logResponse(method, url, xhr.status, xhr.statusText, responseData);
            
            // 模擬fetch API回應格式
            const response = {
                ok: xhr.status >= 200 && xhr.status < 300,
                status: xhr.status,
                statusText: xhr.statusText,
                headers: new Headers(),
                json: () => Promise.resolve(responseData),
                text: () => Promise.resolve(xhr.responseText)
            };
            
            resolve(response);
        };
        
        // 處理錯誤
        xhr.onerror = function() {
            const error = new Error('Network error');
            apiLogger.logError(method, url, error);
            reject(error);
        };
        
        // 發送請求
        xhr.send(body);
    });
}

// 向後兼容接口，保持與原來fetch風格一致
async function loggedFetch(url, options = {}) {
    return loggedXHR(url, options);
}

// DOM 元素
const pages = document.querySelectorAll(".page");
const menuItems = document.querySelectorAll(".menu-item");
const actionButtons = document.querySelectorAll(".action-btn");
const authTabs = document.querySelectorAll(".auth-tab");
const authForms = document.querySelectorAll(".auth-form");
const authContainer = document.querySelector(".auth-container");
const welcomeContainer = document.querySelector(".welcome-container");

// 工具函數
// 格式化時間戳
function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('zh-TW');
}

// 格式化日期
function formatDate(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('zh-TW');
}

// 格式化時間
function formatTime(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString('zh-TW');
}

// 顯示通知
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = '';
    if (type === 'success') {
        icon = '<i class="fas fa-check-circle"></i>';
    } else if (type === 'error') {
        icon = '<i class="fas fa-exclamation-circle"></i>';
    } else {
        icon = '<i class="fas fa-info-circle"></i>';
    }
    
    toast.innerHTML = `${icon} <span>${message}</span>`;
    
    const container = document.getElementById('toast-container');
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// 本地儲存 Session
function saveSession(sessionData) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(sessionData));
}

// 讀取 Session
function loadSession() {
    const sessionStr = localStorage.getItem(SESSION_KEY);
    if (sessionStr) {
        try {
            return JSON.parse(sessionStr);
        } catch (e) {
            console.error('Session 解析錯誤:', e);
        }
    }
    return null;
}

// 清除 Session
function clearSession() {
    localStorage.removeItem(SESSION_KEY);
}

// 檢查是否登入
function isLoggedIn() {
    const session = loadSession();
    return session && session.access_token && session.user_id;
}

// 切換頁面
function switchPage(pageName) {
    // 隱藏所有頁面
    pages.forEach(page => page.classList.remove('active'));
    
    // 顯示選定頁面
    const activePage = document.getElementById(`${pageName}-page`);
    if (activePage) {
        activePage.classList.add('active');
    }
    
    // 更新選單項目激活狀態
    menuItems.forEach(item => {
        if (item.getAttribute('data-page') === pageName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // 根據頁面執行初始化
    if (pageName === 'clock') {
        initClockPage();
    } else if (pageName === 'records') {
        initRecordsPage();
    } else if (pageName === 'salary') {
        initSalaryPage();
    }
}

// 登入後的界面初始化
function initLoggedInUI() {
    const session = loadSession();
    if (!session) return;
    
    // 更新使用者資訊
    document.getElementById('username').textContent = session.user_id;
    document.getElementById('welcome-username').textContent = session.user_id;
    document.getElementById('welcome-role').textContent = (session.role === 'employee' ? '員工' : '主管');
    
    // 顯示登出按鈕
    document.getElementById('logout-btn').classList.remove('hidden');
    
    // 隱藏身份驗證容器，顯示歡迎容器
    authContainer.classList.add('hidden');
    welcomeContainer.classList.remove('hidden');
    
    // 檢查登入狀態並載入今日打卡狀態
    checkLoginStatus();
    loadTodayClockStatus();
}

// 登出後的界面初始化
function initLoggedOutUI() {
    // 更新使用者資訊
    document.getElementById('username').textContent = '未登入';
    
    // 隱藏登出按鈕
    document.getElementById('logout-btn').classList.add('hidden');
    
    // 顯示身份驗證容器，隱藏歡迎容器
    authContainer.classList.remove('hidden');
    welcomeContainer.classList.add('hidden');
    
    // 切換到首頁
    switchPage('home');
}

// 刷新 Token
async function refreshToken() {
    const session = loadSession();
    if (!session || !session.refresh_token || !session.user_id) return false;
    
    try {
        const response = await loggedFetch(`${BASE_URL}/authorization/refreshToken`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                refresh_token: session.refresh_token,
                user_id: session.user_id
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            session.access_token = data.new_access_token;
            session.refresh_token = data.new_refresh_token;
            saveSession(session);
            return true;
        } else {
            showToast('Token 已過期，請重新登入', 'error');
            return false;
        }
    } catch (error) {
        console.error('刷新 Token 發生錯誤:', error);
        showToast('連接伺服器失敗，請稍後再試', 'error');
        return false;
    }
}

// 檢查登入狀態
async function checkLoginStatus() {
    const session = loadSession();
    if (!session || !session.access_token || !session.user_id) {
        initLoggedOutUI();
        return false;
    }
      try {
        // 使用GET請求但帶有body
        const response = await loggedFetch(`${BASE_URL}/authorization/authorize`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                access_token: session.access_token,
                user_id: session.user_id
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.result === 'Valid') {
                return true;
            } else if (result.result === 'Expired') {
                // Token 已過期，嘗試刷新
                const refreshed = await refreshToken();
                if (!refreshed) {
                    // 刷新失敗，清除 Session 並返回登入頁面
                    clearSession();
                    initLoggedOutUI();
                }
                return refreshed;
            } else {
                // Token 無效
                clearSession();
                initLoggedOutUI();
                return false;
            }
        } else {
            throw new Error('無法檢查登入狀態');
        }
    } catch (error) {
        console.error('檢查登入狀態時發生錯誤:', error);
        // 保留 Session，可能是暫時性網路問題
        return false;
    }
}

// 初始化時鐘顯示
function initClock() {
    function updateClock() {
        const now = new Date();
        const timeElement = document.getElementById('current-time');
        const dateElement = document.getElementById('current-date');
        
        // 格式化時間
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        timeElement.textContent = `${hours}:${minutes}:${seconds}`;
        
        // 格式化日期
        const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
        const month = now.getMonth() + 1;
        const date = now.getDate();
        const weekday = weekdays[now.getDay()];
        dateElement.textContent = `${month} 月 ${date} 日 星期${weekday}`;
    }
    
    // 立即更新一次
    updateClock();
    // 每秒更新一次
    setInterval(updateClock, 1000);
}

// 載入今日打卡狀態
async function loadTodayClockStatus() {
    const session = loadSession();
    if (!session) return;
    
    // 計算今天的開始時間
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const startTime = Math.floor(today.getTime() / 1000);
    const endTime = Math.floor(Date.now() / 1000);
    
    try {
        const todayStatusElement = document.getElementById('today-clock-status');
        const todayTimeElement = document.getElementById('today-clock-time');
        const todayRecordsElement = document.getElementById('today-records-container');
        const todayRecordsLoading = document.getElementById('today-records-loading');
        
        if (todayRecordsLoading) {
            todayRecordsLoading.classList.remove('hidden');
        }
        
        const headers = {
            'Authorization': session.access_token,
            'X-User-ID': session.user_id
        };
          // 使用GET請求帶body
        const response = await loggedFetch(`${BASE_URL}/employee/records`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': session.access_token,
                'X-User-ID': session.user_id
            },
            body: JSON.stringify({
                user_id: session.user_id,
                start_time: startTime,
                end_time: endTime
            })
        });
        
        if (todayRecordsLoading) {
            todayRecordsLoading.classList.add('hidden');
        }
        
        if (response.ok) {
            const result = await response.json();
            if (result.status === 'success' && result.data) {
                const records = result.data;
                
                // 更新首頁的今日狀態
                if (records.length > 0) {
                    // 按時間排序
                    records.sort((a, b) => b.time - a.time);
                    
                    // 找到最新的一筆
                    const latestRecord = records[0];
                    
                    todayStatusElement.textContent = latestRecord.type === 'i' ? '已上班打卡' : '已下班打卡';
                    todayTimeElement.textContent = formatTime(latestRecord.time);
                } else {
                    todayStatusElement.textContent = '尚未打卡';
                    todayTimeElement.textContent = '';
                }
                
                // 更新打卡頁面的今日記錄
                if (todayRecordsElement) {
                    if (records.length > 0) {
                        let recordsHTML = '';
                        records.forEach((record, index) => {
                            recordsHTML += `
                                <div class="record-item">
                                    <div class="record-time">${formatTime(record.time)}</div>
                                    <div class="record-type ${record.type === 'i' ? 'type-in' : 'type-out'}">
                                        ${record.type === 'i' ? '上班打卡' : '下班打卡'}
                                    </div>
                                </div>
                            `;
                        });
                        todayRecordsElement.innerHTML = recordsHTML;
                    } else {
                        todayRecordsElement.innerHTML = '<div class="no-records">今日尚未有打卡記錄</div>';
                    }
                }
            } else {
                showToast('獲取打卡記錄失敗', 'error');
                todayStatusElement.textContent = '載入失敗';
                if (todayRecordsElement) {
                    todayRecordsElement.innerHTML = '<div class="no-records">無法載入打卡記錄</div>';
                }
            }
        } else {
            throw new Error('API 請求失敗');
        }
    } catch (error) {
        console.error('載入今日打卡狀態時發生錯誤:', error);
        showToast('載入打卡狀態失敗，請重新整理頁面', 'error');
    }
}

// 初始化打卡頁面
function initClockPage() {
    if (!isLoggedIn()) {
        showToast('請先登入', 'error');
        switchPage('home');
        return;
    }
    
    loadTodayClockStatus();
}

// 初始化打卡記錄頁面
function initRecordsPage() {
    if (!isLoggedIn()) {
        showToast('請先登入', 'error');
        switchPage('home');
        return;
    }
    
    // 設定預設日期範圍（當月）
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    
    const startDateInput = document.getElementById('records-start-date');
    const endDateInput = document.getElementById('records-end-date');
    
    startDateInput.value = firstDayOfMonth.toISOString().split('T')[0];
    endDateInput.value = today.toISOString().split('T')[0];
    
    // 先不自動查詢，讓使用者點擊按鈕
}

// 初始化薪資頁面
function initSalaryPage() {
    if (!isLoggedIn()) {
        showToast('請先登入', 'error');
        switchPage('home');
        return;
    }
    
    querySalary();
}

// 註冊功能
async function registerEmployee() {
    // 獲取表單數據
    const account = document.getElementById('register-account').value.trim();
    const password = document.getElementById('register-password').value.trim();
    const bossId = document.getElementById('register-boss').value.trim();
    const messageElement = document.getElementById('register-message');
    
    // 表單驗證
    if (!account || !password || !bossId) {
        messageElement.textContent = '請填寫所有欄位';
        messageElement.style.color = 'red';
        return;
    }
    
    try {
        const response = await loggedFetch(`${BASE_URL}/employee/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                account,
                password,
                boss_id: bossId
            })
        });
        
        const result = await response.json();
        if (response.ok && result.status === 'success') {
            messageElement.textContent = '註冊成功！請切換到登入頁面';
            messageElement.style.color = 'green';
            
            // 清空表單
            document.getElementById('register-account').value = '';
            document.getElementById('register-password').value = '';
            document.getElementById('register-boss').value = '';
            
            // 3秒後切換到登入頁籤
            setTimeout(() => {
                switchAuthTab('login');
            }, 3000);
            
            showToast('註冊成功', 'success');
        } else {
            messageElement.textContent = result.message || '註冊失敗';
            messageElement.style.color = 'red';
            showToast('註冊失敗', 'error');
        }
    } catch (error) {
        console.error('註冊過程中發生錯誤:', error);
        messageElement.textContent = '註冊過程中發生錯誤，請稍後再試';
        messageElement.style.color = 'red';
        showToast('連接伺服器失敗', 'error');
    }
}

// 登入功能
async function login() {
    // 獲取表單數據
    const account = document.getElementById('login-account').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const role = document.getElementById('login-role').value;
    const messageElement = document.getElementById('login-message');
    
    // 表單驗證
    if (!account || !password) {
        messageElement.textContent = '請填寫所有欄位';
        messageElement.style.color = 'red';
        return;
    }
    
    try {
        const response = await loggedFetch(`${BASE_URL}/api/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                account,
                password,
                role
            })
        });
        
        const result = await response.json();
        if (response.ok && result.status === 'success' && result.data) {
            // 儲存登入資訊
            const sessionData = {
                access_token: result.data.access_token,
                refresh_token: result.data.refresh_token,
                user_id: account,
                role: role
            };
            saveSession(sessionData);
            
            // 顯示成功訊息
            messageElement.textContent = '登入成功！';
            messageElement.style.color = 'green';
            
            // 清空表單
            document.getElementById('login-account').value = '';
            document.getElementById('login-password').value = '';
            
            // 初始化已登入的界面
            initLoggedInUI();
            showToast('登入成功', 'success');
        } else {
            messageElement.textContent = result.message || '登入失敗';
            messageElement.style.color = 'red';
            showToast('登入失敗', 'error');
        }
    } catch (error) {
        console.error('登入過程中發生錯誤:', error);
        messageElement.textContent = '登入過程中發生錯誤，請稍後再試';
        messageElement.style.color = 'red';
        showToast('連接伺服器失敗', 'error');
    }
}

// 登出功能
function logout() {
    // 清除登入資訊
    clearSession();
    
    // 初始化登出後的界面
    initLoggedOutUI();
    showToast('登出成功', 'success');
}

// 上下班打卡功能
async function clockInOut(type) {
    // 檢查登入狀態
    if (!isLoggedIn()) {
        showToast('請先登入', 'error');
        switchPage('home');
        return;
    }
    
    const session = loadSession();
    const statusElement = document.getElementById('clock-status-message');
    
    try {
        // 檢查 token 是否有效
        const isValid = await checkLoginStatus();
        if (!isValid) {
            showToast('認證已過期，請重新登入', 'error');
            return;
        }
        
        // 設定 HTTP 標頭
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': session.access_token,
            'X-User-ID': session.user_id
        };
        
        // 準備打卡數據
        const clockTime = Math.floor(Date.now() / 1000);
        
        // 發送打卡請求
        const response = await loggedFetch(`${BASE_URL}/employee/records`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                user_id: session.user_id,
                type: type,
                time: clockTime
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.status === 'success') {
                statusElement.textContent = `${type === 'i' ? '上班' : '下班'}打卡成功！`;
                statusElement.style.color = 'green';
                
                // 重新載入今日打卡狀態
                loadTodayClockStatus();
                showToast(`${type === 'i' ? '上班' : '下班'}打卡成功`, 'success');
            } else {
                statusElement.textContent = result.message || '打卡失敗';
                statusElement.style.color = 'red';
                showToast('打卡失敗', 'error');
            }
        } else {
            throw new Error('API 請求失敗');
        }
    } catch (error) {
        console.error('打卡過程中發生錯誤:', error);
        statusElement.textContent = '打卡過程中發生錯誤，請稍後再試';
        statusElement.style.color = 'red';
        showToast('連接伺服器失敗', 'error');
    }
}

// 查詢打卡記錄
async function queryRecords() {
    // 檢查登入狀態
    if (!isLoggedIn()) {
        showToast('請先登入', 'error');
        switchPage('home');
        return;
    }
    
    const session = loadSession();
    const loadingElement = document.getElementById('records-loading');
    const tableBodyElement = document.getElementById('records-table-body');
    const noRecordsElement = document.getElementById('no-records-message');
    
    // 獲取日期範圍
    const startDateStr = document.getElementById('records-start-date').value;
    const endDateStr = document.getElementById('records-end-date').value;
    
    // 轉換為 UNIX timestamp
    const startDate = new Date(startDateStr);
    startDate.setHours(0, 0, 0, 0);
    const startTime = Math.floor(startDate.getTime() / 1000);
    
    const endDate = new Date(endDateStr);
    endDate.setHours(23, 59, 59, 999);
    const endTime = Math.floor(endDate.getTime() / 1000);
    
    // 驗證日期範圍
    if (startTime > endTime) {
        showToast('起始日期不能晚於結束日期', 'error');
        return;
    }
    
    try {
        // 顯示加載動畫
        loadingElement.classList.remove('hidden');
        tableBodyElement.innerHTML = '';
        noRecordsElement.classList.add('hidden');
        
        // 設定 HTTP 標頭
        const headers = {
            'Authorization': session.access_token,
            'X-User-ID': session.user_id
        };
          // 使用GET請求帶body
        const response = await loggedFetch(`${BASE_URL}/employee/records`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': session.access_token,
                'X-User-ID': session.user_id
            },
            body: JSON.stringify({
                user_id: session.user_id,
                start_time: startTime,
                end_time: endTime
            })
        });
        
        // 隱藏加載動畫
        loadingElement.classList.add('hidden');
        
        if (response.ok) {
            const result = await response.json();
            console.log(result); // 調試用
            
            if (result.status === 'success' && result.data) {
                const records = result.data;
                
                if (records.length > 0) {
                    // 按時間排序，最新的在前
                    records.sort((a, b) => b.time - a.time);
                    
                    // 構建表格內容
                    let tableContent = '';
                    records.forEach((record, index) => {
                        const date = formatDate(record.time);
                        const time = formatTime(record.time);
                        const type = record.type === 'i' ? '上班' : '下班';
                        
                        tableContent += `
                            <tr>
                                <td>${index + 1}</td>
                                <td>${date}</td>
                                <td>${time}</td>
                                <td>${type}</td>
                            </tr>
                        `;
                    });
                    
                    tableBodyElement.innerHTML = tableContent;
                } else {
                    // 無記錄
                    noRecordsElement.classList.remove('hidden');
                }
            } else {
                showToast('獲取打卡記錄失敗', 'error');
                noRecordsElement.classList.remove('hidden');
                noRecordsElement.textContent = '獲取數據失敗，請稍後再試';
            }
        } else {
            throw new Error('API 請求失敗');
        }
    } catch (error) {
        console.error('查詢打卡記錄時發生錯誤:', error);
        loadingElement.classList.add('hidden');
        noRecordsElement.classList.remove('hidden');
        noRecordsElement.textContent = '連接伺服器失敗，請稍後再試';
        showToast('連接伺服器失敗', 'error');
    }
}

// 查詢薪資
async function querySalary() {
    // 檢查登入狀態
    if (!isLoggedIn()) {
        showToast('請先登入', 'error');
        switchPage('home');
        return;
    }
    
    const session = loadSession();
    const loadingElement = document.getElementById('salary-loading');
    const salaryCardElement = document.getElementById('salary-card');
    const noSalaryElement = document.getElementById('no-salary-message');
    
    try {
        // 顯示加載動畫
        loadingElement.classList.remove('hidden');
        salaryCardElement.classList.add('hidden');
        noSalaryElement.classList.add('hidden');
        
        // 檢查 token 是否有效
        const isValid = await checkLoginStatus();
        if (!isValid) {
            showToast('認證已過期，請重新登入', 'error');
            return;
        }
        
        // 設定 HTTP 標頭
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': session.access_token,
            'X-User-ID': session.user_id
        };
        
        // 發送查詢請求
        const response = await loggedFetch(`${BASE_URL}/employee/salary`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                user_id: session.user_id
            })
        });
        
        // 隱藏加載動畫
        loadingElement.classList.add('hidden');
        
        if (response.ok) {
            const result = await response.json();
            console.log(result); // 調試用
            
            if (result.status === 'success' && result.data) {
                const salaryData = result.data;
                
                // 更新薪資卡片
                document.getElementById('salary-user-id').textContent = session.user_id;
                
                // 處理薪資數據
                if (Array.isArray(salaryData) && salaryData.length > 0) {
                    // 如果是陣列，取第一筆
                    const salary = salaryData[0].salary;
                    document.getElementById('salary-amount').textContent = `NT$ ${Number(salary).toLocaleString('zh-TW')}`;
                } else if (typeof salaryData === 'object') {
                    // 如果是單一物件
                    const salary = salaryData.salary;
                    document.getElementById('salary-amount').textContent = `NT$ ${Number(salary).toLocaleString('zh-TW')}`;
                } else {
                    // 無法處理的數據格式
                    throw new Error('無法解析薪資數據');
                }
                
                // 更新時間
                document.getElementById('salary-update-time').textContent = new Date().toLocaleString('zh-TW');
                
                // 顯示薪資卡片
                salaryCardElement.classList.remove('hidden');
            } else {
                // 無薪資數據
                noSalaryElement.classList.remove('hidden');
            }
        } else {
            throw new Error('API 請求失敗');
        }
    } catch (error) {
        console.error('查詢薪資時發生錯誤:', error);
        loadingElement.classList.add('hidden');
        noSalaryElement.classList.remove('hidden');
        noSalaryElement.textContent = '連接伺服器失敗，請稍後再試';
        showToast('連接伺服器失敗', 'error');
    }
}

// 切換身份驗證標籤
function switchAuthTab(tab) {
    // 更新標籤激活狀態
    authTabs.forEach(tabEl => {
        if (tabEl.getAttribute('data-tab') === tab) {
            tabEl.classList.add('active');
        } else {
            tabEl.classList.remove('active');
        }
    });
    
    // 更新表單顯示
    authForms.forEach(formEl => {
        if (formEl.id === `${tab}-form`) {
            formEl.classList.add('active');
        } else {
            formEl.classList.remove('active');
        }
    });
}

// 事件監聽器
document.addEventListener('DOMContentLoaded', function() {
    // 初始化時鐘
    initClock();
    
    // 根據登入狀態初始化界面
    if (isLoggedIn()) {
        initLoggedInUI();
    } else {
        initLoggedOutUI();
    }
    
    // 選單項目點擊事件
    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.getAttribute('data-page');
            switchPage(page);
        });
    });
    
    // 歡迎頁面上的動作按鈕
    actionButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const page = btn.getAttribute('data-page');
            switchPage(page);
        });
    });
    
    // 身份驗證標籤切換
    authTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.getAttribute('data-tab');
            switchAuthTab(tabName);
        });
    });
    
    // 註冊按鈕點擊事件
    document.getElementById('register-button').addEventListener('click', registerEmployee);
    
    // 登入按鈕點擊事件
    document.getElementById('login-button').addEventListener('click', login);
    
    // 登出按鈕點擊事件
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    // 打卡按鈕點擊事件
    document.getElementById('clock-in-btn').addEventListener('click', () => clockInOut('i'));
    document.getElementById('clock-out-btn').addEventListener('click', () => clockInOut('o'));
    
    // 查詢記錄按鈕點擊事件
    document.getElementById('query-records-btn').addEventListener('click', queryRecords);
});
