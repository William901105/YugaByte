// 全局的登出處理函數
function handleLogout(message = null) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('refresh_token');
    if (message) {
        sessionStorage.setItem('error_message', message);
    }
    window.location.href = 'index.html';
}

// 全局的認證檢查函數
async function checkAuthorization() {
    const access_token = localStorage.getItem('access_token');
    const user_id = localStorage.getItem('user_id');

    if (!access_token || !user_id) {
        handleLogout('認證信息缺失，請重新登入');
        return false;
    }

    try {
        const response = await fetch('/authorization/authorize', {
            method: 'GET',
            headers: {
                'Authorization': access_token,
                'User-Id': user_id // /authorization/authorize 端點使用 User-Id
            }
        });

        const data = await response.json();

        if (response.ok) {
            if (data.result === 'NeedsRefresh') {
                localStorage.setItem('access_token', data.new_access_token);
                localStorage.setItem('refresh_token', data.new_refresh_token);
                return true;
            } else if (data.result === 'Valid') {
                return true;
            } else {
                handleLogout(data.message || `認證回應無效 (${data.result})，請重新登入`);
                return false;
            }
        } else {
            const errorMessage = data.result || data.message || '認證服務器錯誤';
             if (data.result === 'Invalid' || data.result === 'Expired') {
                 handleLogout(`認證${data.result === 'Expired' ? '已過期' : '無效'}，請重新登入`);
            } else {
                 handleLogout(`認證檢查失敗: ${errorMessage}`);
            }
            return false;
        }
    } catch (error) {
        console.error('Authorization check critical error:', error);
        handleLogout('認證檢查時發生系統錯誤，請重新登入');
        return false;
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    // 執行初始認證檢查
    if (!await checkAuthorization()) {
        return; // 中止薪資頁面的進一步設定
    }

    // 如果程式執行到這裡，表示認證成功
    // 設置預設日期範圍（本月）
    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDayOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    document.getElementById('startDate').value = formatDate(firstDayOfMonth);
    document.getElementById('endDate').value = formatDate(lastDayOfMonth);
    
    // 登出按鈕 (假設HTML中有一個登出按鈕，例如 id="logoutBtn")
    const logoutBtn = document.getElementById('logoutBtn'); 
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            handleLogout(); 
        });
    }

    // 查詢按鈕
    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
        searchBtn.addEventListener('click', searchSalary);
    }

    // 初始查詢
    searchSalary();
});

// 格式化日期為 YYYY-MM-DD
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 將日期字符串轉換為時間戳 (秒)
function dateToTimestamp(dateStr) {
    const date = new Date(dateStr);
    return Math.floor(date.getTime() / 1000);
}

// 查詢薪資
async function searchSalary() {
    const startDateValue = document.getElementById('startDate').value;
    const endDateValue = document.getElementById('endDate').value;
    
    if (!startDateValue || !endDateValue) {
        alert('請選擇日期範圍');
        return;
    }

    const startTime = dateToTimestamp(startDateValue);
    // 結束時間戳需要包含當天整天，所以加到當天結束 (23:59:59)
    const endTime = dateToTimestamp(endDateValue) + (24 * 60 * 60 -1); 

    const token = localStorage.getItem('access_token');
    const bossId = localStorage.getItem('user_id');

    if (!token || !bossId) {
        handleLogout('查詢薪資時認證信息丢失，請重新登入');
        return;
    }

    try {
        // 注意：後端 /boss/subordinate_salary 預期 start_time 和 end_time 作為 URL 查詢參數
        // 並且根據 api.py，它似乎還預期一個 JSON body 包含 user_id (儘管這個 GET 請求通常不帶 body)
        // 我們需要確認 /boss/subordinate_salary 的確切接口。假設它現在不需要 user_id in body for boss role.
        const response = await fetch(`/boss/subordinate_salary?start_time=${startTime}&end_time=${endTime}`, {
            method: 'GET', // 確認是否真的是 GET，或者後端期望 POST 帶 JSON body
            headers: {
                'Authorization': token,
                'X-User-ID': bossId, // 確認後端 verify_boss_access 是否使用 X-User-ID
                'Accept': 'application/json'
                // 'Content-Type': 'application/json' // 如果是 POST 且有 body，則需要此行
            },
            // body: JSON.stringify({ user_id: bossId }) // 如果後端需要 user_id in body for boss role
        });

        if (response.status === 401) {
            handleLogout('會話已過期，請重新登入');
            return;
        }
        
        const data = await response.json();

        if (!response.ok) {
             // 使用 data 中的 message 或提供通用錯誤
            throw new Error(data.message || `獲取薪資資料失敗 (HTTP ${response.status})`);
        }
        
        displaySalaryData(data.data || []);
    } catch (error) {
        console.error('Error searching salary:', error);
        if (error.message && (error.message.toLowerCase().includes('認證') || error.message.toLowerCase().includes('過期')|| error.message.toLowerCase().includes('會話'))) {
            handleLogout('查詢薪資資料時認證失敗或會話過期，請重新登入');
        } else {
            alert('查詢薪資資料時發生錯誤：' + error.message);
        }
    }
}

// 顯示薪資數據
function displaySalaryData(data) {
    const tableBody = document.getElementById('salaryTableBody');
    const statsDiv = document.getElementById('salaryStats');
    
    tableBody.innerHTML = '';
    statsDiv.innerHTML = '';

    if (!Array.isArray(data) || data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="no-data">該時間範圍內無薪資記錄</td></tr>';
        return;
    }

    let totalBaseSalary = 0;
    let totalOvertime = 0;
    let totalLatePenalty = 0;
    let totalAbsentPenalty = 0;
    let totalFinalSalary = 0;

    data.forEach(employee => {
        const row = document.createElement('tr');
        // 後端返回的 subordinate_salary 結構可能需要調整以匹配此處的欄位
        // 例如 employee.base_salary, employee.overtime_pay 等
        row.innerHTML = `
            <td>${employee.user_id}</td>
            <td>${(employee.base_salary || 0).toFixed(2)}</td>
            <td>${(employee.overtime_pay || 0).toFixed(2)}</td>
            <td>${(employee.late_penalty || 0).toFixed(2)}</td>
            <td>${(employee.absent_penalty || 0).toFixed(2)}</td>
            <td>${(employee.final_salary || 0).toFixed(2)}</td>
        `;
        tableBody.appendChild(row);

        totalBaseSalary += (employee.base_salary || 0);
        totalOvertime += (employee.overtime_pay || 0);
        totalLatePenalty += (employee.late_penalty || 0);
        totalAbsentPenalty += (employee.absent_penalty || 0);
        totalFinalSalary += (employee.final_salary || 0);
    });

    statsDiv.innerHTML = `
        <div class="stats-grid">
            <div class="stat-item">
                <label>總基本薪資：</label>
                <span>${totalBaseSalary.toFixed(2)}</span>
            </div>
            <div class="stat-item">
                <label>總加班費：</label>
                <span>${totalOvertime.toFixed(2)}</span>
            </div>
            <div class="stat-item">
                <label>總遲到扣款：</label>
                <span>${totalLatePenalty.toFixed(2)}</span>
            </div>
            <div class="stat-item">
                <label>總缺勤扣款：</label>
                <span>${totalAbsentPenalty.toFixed(2)}</span>
            </div>
            <div class="stat-item">
                <label>總實領薪資：</label>
                <span>${totalFinalSalary.toFixed(2)}</span>
            </div>
        </div>
    `;
}

// 定期檢查認證狀態
setInterval(checkAuthorization, 60000); // 每 60 秒檢查一次 