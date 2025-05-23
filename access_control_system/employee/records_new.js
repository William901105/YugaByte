/**
 * 員工打卡記錄查詢系統的主要JavaScript文件
 * 
 * 功能說明：
 * 1. 提供日期範圍選擇功能
 * 2. 查詢指定期間的打卡記錄
 * 3. 顯示記錄的詳細資訊
 * 4. 整合 Token 驗證機制
 */

document.addEventListener('DOMContentLoaded', function () {
    const userId = localStorage.getItem('user_id');
    const accessToken = localStorage.getItem('access_token');

    // 驗證登入狀態
    if (!userId || !accessToken) {
        alert('未登入或登入已過期，請重新登入');
        window.location.href = 'index.html';
        return;
    }

    // 初始化元素
    const dateRangeForm = document.getElementById('dateRangeForm');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessage = document.getElementById('errorMessage');
    const recordsTable = document.getElementById('recordsTable');
    const noRecordsMessage = document.getElementById('noRecordsMessage');

    // 設置今天作為結束日期的預設值
    const today = new Date();
    endDateInput.value = today.toISOString().split('T')[0];
    
    // 設置一個月前作為開始日期的預設值
    const oneMonthAgo = new Date(today.setMonth(today.getMonth() - 1));
    startDateInput.value = oneMonthAgo.toISOString().split('T')[0];    // 驗證 token
    async function verifyToken() {
        try {
            console.log('發送 Token 驗證請求 - 方法: POST, URL: /authorization/authorize');
            console.log('請求參數:', JSON.stringify({
                access_token: accessToken,
                user_id: userId
            }));

            const response = await fetch('http://localhost:5000/authorization/authorize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    access_token: accessToken,
                    user_id: userId
                })
            });

            const data = await response.json();
            console.log('Token 驗證回應:', JSON.stringify(data));
            
            if (data.result === 'Expired') {
                // Token 過期，嘗試刷新
                return await refreshToken();
            }
            
            return data.result === 'Valid';
        } catch (error) {
            console.error('Token 驗證錯誤:', error);
            return false;
        }
    }    // 刷新 token
    async function refreshToken() {
        try {
            const refreshToken = localStorage.getItem('refresh_token');
            
            console.log('發送 Token 刷新請求 - 方法: POST, URL: /authorization/refreshToken');
            console.log('請求參數:', JSON.stringify({
                refresh_token: refreshToken,
                user_id: userId
            }));
            
            const response = await fetch('http://localhost:5000/authorization/refreshToken', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    refresh_token: refreshToken,
                    user_id: userId
                })
            });

            const data = await response.json();
            console.log('Token 刷新回應:', JSON.stringify(data));
            
            if (response.ok) {
                localStorage.setItem('access_token', data.new_access_token);
                localStorage.setItem('refresh_token', data.new_refresh_token);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Token 刷新錯誤:', error);
            return false;
        }
    }

    // 查詢打卡記錄
    async function fetchRecords(startDate, endDate) {
        try {
            loadingIndicator.style.display = 'block';
            errorMessage.style.display = 'none';
            noRecordsMessage.style.display = 'none';

            // 先驗證 token
            const isValid = await verifyToken();
            if (!isValid) {
                throw new Error('認證已過期，請重新登入');
            }
            
            // 轉換日期格式為時間戳
            const start = Math.floor(new Date(startDate).getTime() / 1000);
            const end = Math.floor(new Date(endDate).getTime() / 1000 + 86399); // 加上一天減1秒            // 查詢員工打卡記錄
            const requestBody = {
                user_id: userId,
                start_time: start,
                end_time: end
            };
            console.log('發送打卡記錄查詢請求 - 方法: POST, URL: /employee/records');
            console.log('請求參數:', JSON.stringify(requestBody));
            console.log('請求頭:', JSON.stringify({
                'Content-Type': 'application/json',
                'Authorization': accessToken,
                'X-User-ID': userId
            }));
            
            const response = await fetch('http://localhost:5000/employee/records', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': accessToken,
                    'X-User-ID': userId
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();
            console.log('打卡記錄查詢回應:', JSON.stringify(data));
            
            if (data.status !== 'success') {
                throw new Error(data.message || '查詢失敗');
            }

            // 更新表格
            const tbody = recordsTable.querySelector('tbody');
            tbody.innerHTML = ''; // 清空現有內容

            if (data.data.length === 0) {
                noRecordsMessage.style.display = 'block';
                return;
            }

            // 按照時間排序，最新的記錄在前面
            data.data.sort((a, b) => b.time - a.time);

            data.data.forEach(record => {
                const row = document.createElement('tr');
                const date = new Date(record.time * 1000);
                
                row.innerHTML = `
                    <td>${date.toLocaleDateString('zh-TW')}</td>
                    <td>${record.type === 'i' ? '上班' : '下班'}</td>
                    <td>${date.toLocaleTimeString('zh-TW')}</td>
                `;
                
                tbody.appendChild(row);
            });

        } catch (error) {
            console.error('查詢打卡記錄錯誤:', error);
            errorMessage.textContent = error.message;
            errorMessage.style.display = 'block';
              if (error.message.includes('認證已過期')) {
                localStorage.clear();
                console.log('認證已過期，但不會自動跳轉，便於查看錯誤');
                // 註解掉自動跳轉，方便查看錯誤
                // setTimeout(() => {
                //    window.location.href = 'index.html';
                // }, 2000);
            }
        } finally {
            loadingIndicator.style.display = 'none';
        }
    }

    // 表單提交事件
    dateRangeForm.addEventListener('submit', function (e) {
        e.preventDefault();
        fetchRecords(startDateInput.value, endDateInput.value);
    });

    // 登出功能
    document.getElementById('logoutButton').addEventListener('click', function () {
        localStorage.clear();
        window.location.href = 'index.html';
    });

    // 初始載入
    fetchRecords(startDateInput.value, endDateInput.value);
});
