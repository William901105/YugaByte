/**
 * 員工薪資查詢系統的主要JavaScript文件
 * 
 * 功能說明：
 * 1. 查詢個人薪資資訊
 * 2. 處理 token 驗證和更新
 * 3. 自動重新整理過期的 access token
 * 4. 顯示薪資明細和計算結果
 * 5. 處理錯誤狀態和重試機制
 * 
 * API端點：
 * - GET /api/salary：獲取薪資資訊
 * - POST /authorization/refreshToken：更新過期的 token
 * 
 * 安全機制：
 * - 使用 Bearer token 進行身份驗證
 * - 實作 refresh token 機制
 * - 自動處理登入過期重導向
 * 
 * 本地儲存：
 * - accessToken：API 存取權杖
 * - refreshToken：更新用權杖
 * - userId：用戶識別碼
 */

document.addEventListener('DOMContentLoaded', async function () {
    // 驗證 token 和用戶資訊
    const accessToken = localStorage.getItem('accessToken');
    const refreshToken = localStorage.getItem('refreshToken');
    const userId = localStorage.getItem('userId');

    if (!accessToken || !refreshToken || !userId) {
        window.location.href = 'login.html';
    }

    // DOM 元素
    const salaryInfo = document.getElementById('salaryInfo');
    const retryButton = document.getElementById('retryButton');
    const logoutButton = document.getElementById('logoutButton');

    // 查詢薪資資訊
    async function fetchSalary() {
        try {
            salaryInfo.textContent = '載入中...';
            retryButton.style.display = 'none';

            const response = await fetch('http://localhost:5000/api/salary', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'X-User-ID': userId,
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (response.status === 401) {
                // Token 過期，嘗試重新整理
                const refreshResponse = await fetch('http://localhost:5000/authorization/refreshToken', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        refresh_token: refreshToken,
                        user_id: userId
                    })
                });

                if (refreshResponse.ok) {
                    const refreshData = await refreshResponse.json();
                    localStorage.setItem('accessToken', refreshData.access_token);
                    // 重新嘗試獲取薪資資訊
                    return fetchSalary();
                } else {
                    // 重新整理 token 失敗，需要重新登入
                    localStorage.clear();
                    window.location.href = 'login.html';
                    return;
                }
            }

            if (data.status === 'success') {
                const salary = data.data.base_salary;
                salaryInfo.innerHTML = `
                    <div class="info-item">
                        <strong>員工編號：</strong> ${userId}
                    </div>
                    <div class="info-item">
                        <strong>基本薪資：</strong> NT$ ${salary.toLocaleString()}
                    </div>
                `;
            } else {
                throw new Error(data.message || '無法取得薪資資訊');
            }
        } catch (error) {
            console.error('獲取薪資資訊時發生錯誤：', error);
            salaryInfo.textContent = '無法載入薪資資訊';
            retryButton.style.display = 'block';
        }
    }

    // 註冊事件監聽器
    retryButton.addEventListener('click', fetchSalary);

    logoutButton.addEventListener('click', () => {
        localStorage.clear();
        window.location.href = 'login.html';
    });

    // 初始載入
    fetchSalary();
});
