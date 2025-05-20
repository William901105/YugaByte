/**
 * 員工薪資查詢系統的主要JavaScript文件
 * 
 * 功能說明：
 * 1. 查詢個人薪資資訊
 * 2. 處理 token 驗證和更新
 * 3. 自動重新整理過期的 access token
 * 4. 顯示薪資明細
 */

document.addEventListener('DOMContentLoaded', async function () {
    // 驗證 token 和用戶資訊
    const userId = localStorage.getItem('user_id');
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');

    if (!userId || !accessToken || !refreshToken) {
        alert('未登入，請重新登入');
        window.location.href = 'index.html';
        return;
    }

    // DOM 元素
    const salaryInfo = document.getElementById('salaryInfo');
    const retryButton = document.getElementById('retryButton');
    const logoutButton = document.getElementById('logoutButton');

    // 驗證 token
    async function verifyToken() {
        try {
            const response = await fetch('http://localhost:5000/authorization/authorize', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    access_token: accessToken,
                    user_id: userId
                })
            });

            const data = await response.json();
            
            if (data.result === 'Expired') {
                // Token 過期，嘗試刷新
                return await refreshTokenFunc();
            }
            
            return data.result === 'Valid';
        } catch (error) {
            console.error('Token 驗證錯誤:', error);
            return false;
        }
    }

    // 刷新 token
    async function refreshTokenFunc() {
        try {
            const response = await fetch('http://localhost:5000/authorization/refreshToken', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    refresh_token: refreshToken,
                    user_id: userId
                })
            });

            const data = await response.json();
            
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

    // 查詢薪資資訊
    async function fetchSalary() {
        try {
            salaryInfo.textContent = '載入中...';
            retryButton.style.display = 'none';

            // 先驗證 token
            const isValid = await verifyToken();
            if (!isValid) {
                throw new Error('認證已過期，請重新登入');
            }

            // 查詢個人薪資
            const response = await fetch('http://localhost:5000/employee/salary', {
                method: 'GET',
                headers: {
                    'Authorization': accessToken,
                    'X-User-ID': userId,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: userId
                })
            });

            const data = await response.json();

            if (data.status !== 'success') {
                throw new Error(data.message || '查詢失敗');
            }

            // 更新薪資顯示
            if (data.data && data.data.length > 0) {
                const salary = data.data[0].salary;
                salaryInfo.innerHTML = `
                    <div class="info-item">
                        <strong>員工編號：</strong> ${userId}
                    </div>
                    <div class="info-item">
                        <strong>基本薪資：</strong> NT$ ${salary.toLocaleString()}
                    </div>
                `;

                // 同時查詢薪資記錄
                const now = Date.now() / 1000;
                const monthAgo = now - (30 * 24 * 60 * 60);
                
                const logsResponse = await fetch('http://localhost:5000/salary/logs', {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        start_time: monthAgo,
                        end_time: now
                    })
                });

                const logsData = await logsResponse.json();
                
                // 篩選出當前用戶的記錄
                const userLogs = logsData.filter(log => log.user_id === userId);
                
                if (userLogs.length > 0) {
                    let deductions = 0;
                    let bonuses = 0;
                    
                    userLogs.forEach(log => {
                        if (log.type === 'late' || log.type === 'absent') {
                            deductions += (log.duration / 3600) * (salary / 240); // 假設一個月工時240小時
                        } else if (log.type === 'overtime') {
                            bonuses += (log.duration / 3600) * (salary / 240) * 1.5; // 加班費1.5倍
                        }
                    });

                    salaryInfo.innerHTML += `
                        <div class="info-item">
                            <strong>本月扣款：</strong> NT$ ${Math.round(deductions).toLocaleString()}
                        </div>
                        <div class="info-item">
                            <strong>加班費：</strong> NT$ ${Math.round(bonuses).toLocaleString()}
                        </div>
                        <div class="info-item total">
                            <strong>預估實領：</strong> NT$ ${Math.round(salary - deductions + bonuses).toLocaleString()}
                        </div>
                    `;
                }
            } else {
                throw new Error('無薪資資料');
            }
        } catch (error) {
            console.error('查詢薪資錯誤:', error);
            salaryInfo.innerHTML = `<div class="error">${error.message}</div>`;
            retryButton.style.display = 'block';
            
            if (error.message.includes('認證已過期')) {
                localStorage.clear();
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 2000);
            }
        }
    }

    // 重試按鈕
    retryButton.addEventListener('click', fetchSalary);

    // 登出按鈕
    logoutButton.addEventListener('click', function () {
        localStorage.clear();
        window.location.href = 'index.html';
    });

    // 初始查詢
    fetchSalary();
});
