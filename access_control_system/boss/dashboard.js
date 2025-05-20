document.addEventListener('DOMContentLoaded', async () => {
    // 執行初始認證檢查
    if (!await checkAuthorization()) {
        // 如果認證失敗，checkAuthorization 內部已處理登出和重定向
        return; // 中止儀表板的進一步設定
    }

    // 如果程式執行到這裡，表示認證成功 (Token 有效或已更新)
    const bossName = document.getElementById('bossName');
    const employeeList = document.getElementById('employeeList');
    const logoutBtn = document.getElementById('logoutBtn');
    const filterBtn = document.getElementById('filterBtn');
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');

    const bossId = localStorage.getItem('user_id'); // 此時 user_id 應該是有效的

    if (bossId) {
        bossName.textContent = bossId;
    } else {
        // 理論上，如果 checkAuthorization 成功，這裡不應該執行到
        handleLogout('無法獲取用戶資訊，請重新登入');
        return;
    }

    // 登出按鈕事件
    logoutBtn.addEventListener('click', () => {
        handleLogout(); // 用戶主動登出，不需要錯誤訊息
    });

    // 獲取打卡記錄函數
    async function fetchRecords() {
        const current_token = localStorage.getItem('access_token');
        const current_bossId = localStorage.getItem('user_id');
        const current_refresh_token = localStorage.getItem('refresh_token');

        if (!current_token || !current_bossId || !current_refresh_token) {
            handleLogout('獲取資料時認證信息丢失，請重新登入');
            return;
        }

        try {
            const start = new Date(startDate.value).getTime()/1000;
            const end = new Date(endDate.value).getTime() / 1000 + 86400; // 包含結束日期

            const recordResponse = await fetch(`http://localhost:5000/boss/subordinate_record`, {
                method: 'GET',
                headers: {
                    'Authorization': current_token,
                    'X-User-ID': current_bossId, // 注意：這裡使用 X-User-ID
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    "user_id":"Jason",
                    "start_time":start,
                    "end_time":end
                })
            });
            
            if (recordResponse.status === 401) {
                // 如果 API 請求返回 401，表示會話可能已過期
                handleLogout('會話已過期，請重新登入');
                return;
            }
            
            const data = await recordResponse.json();
            
            if (!recordResponse.ok) {
                throw new Error(data.message || '獲取打卡記錄失敗');
            }

            displayRecords(data.data || []);
        } catch (error) {
            console.error('Error fetching records:', error);
            // 對於非認證相關的錯誤，僅提示用戶
            // 認證相關錯誤應由 checkAuthorization 或上述 401 判斷處理
            if (error.message && (error.message.toLowerCase().includes('認證') || error.message.toLowerCase().includes('過期') || error.message.toLowerCase().includes('會話'))) {
                 handleLogout('獲取資料時認證失敗或會話過期，請重新登入');
            } else {
                 alert('獲取資料失敗：' + error.message);
            }
        }
    }

    // 顯示打卡記錄函數
    function displayRecords(records) {
        employeeList.innerHTML = '';
        if (!Array.isArray(records) || records.length === 0) {
            employeeList.innerHTML = '<p class="no-data">該時間範圍內無打卡記錄</p>';
            return;
        }
        const groupedRecords = {};
        records.forEach(record => {
            if (!groupedRecords[record.user_id]) {
                groupedRecords[record.user_id] = [];
            }
            groupedRecords[record.user_id].push(record);
        });
        for (const [employeeId, employeeRecords] of Object.entries(groupedRecords)) {
            const employeeDiv = document.createElement('div');
            employeeDiv.className = 'employee-card';
            const title = document.createElement('h3');
            title.textContent = `員工ID: ${employeeId}`;
            employeeDiv.appendChild(title);
            const recordsList = document.createElement('div');
            recordsList.className = 'record-list';
            employeeRecords.forEach(record => {
                const recordItem = document.createElement('div');
                recordItem.className = 'record-item';
                const date = new Date(record.time * 1000);
                const type = record.type === 'i' ? '上班' : '下班';
                recordItem.textContent = `${type}時間: ${date.toLocaleString()}`;
                recordsList.appendChild(recordItem);
            });
            employeeDiv.appendChild(recordsList);
            employeeList.appendChild(employeeDiv);
        }
    }

    // 設定預設日期並初次載入資料
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    startDate.value = todayStr;
    endDate.value = todayStr;

    filterBtn.addEventListener('click', fetchRecords);
    fetchRecords(); // 頁面載入時初次獲取記錄
});

// 全局的登出處理函數
function handleLogout(message = null) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('refresh_token'); // 確保 refresh token 也被清除
    if (message) {
        sessionStorage.setItem('error_message', message);
    }
    window.location.href = 'index.html'; // 重定向到登入頁面
}

// 全局的認證檢查函數
async function checkAuthorization() {
    const access_token = localStorage.getItem('access_token');
    const user_id = localStorage.getItem('user_id');
    const refresh_token = localStorage.getItem('refresh_token');

    if (!access_token||!refresh_token || !user_id) {
        handleLogout('認證信息缺失，請重新登入');
        return false;
    }

}

// 定期檢查認證狀態
setInterval(checkAuthorization, 60000); // 每 60 秒檢查一次 