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
    const logoutButton = document.getElementById('logoutButton');    // 驗證 token
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
                return await refreshTokenFunc();
            }
            
            return data.result === 'Valid';
        } catch (error) {
            console.error('Token 驗證錯誤:', error);
            return false;
        }
    }    // 刷新 token
    async function refreshTokenFunc() {
        try {
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
        const requestBody = { user_id: userId };
        console.log('發送薪資查詢請求 - 方法: POST, URL: /employee/salary');
        console.log('請求參數:', JSON.stringify(requestBody));
        console.log('請求頭:', JSON.stringify({
            'Authorization': accessToken,
            'X-User-ID': userId,
            'Content-Type': 'application/json'
        }));
        
        // 使用 fetch 的 mode 設置為 'cors'，啟用詳細的 CORS 檢測
        try {
            // CORS 預檢請求檢測
            const optionsResponse = await fetch('http://localhost:5000/employee/salary', {
                method: 'OPTIONS',
                headers: {
                    'Origin': window.location.origin,
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Authorization, X-User-ID, Content-Type'
                }
            }).catch(error => {
                console.error('CORS 預檢請求失敗:', error);
                throw new Error('CORS 預檢請求失敗，可能是伺服器未正確配置 CORS');
            });
            
            console.log('CORS 預檢回應狀態:', optionsResponse.status);
            console.log('CORS 預檢回應標頭:', {
                'Access-Control-Allow-Origin': optionsResponse.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': optionsResponse.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': optionsResponse.headers.get('Access-Control-Allow-Headers')
            });
        } catch (corsError) {
            console.error('CORS 檢測錯誤:', corsError);
            // 繼續執行，因為有些伺服器可能不正確響應 OPTIONS 請求
        }

        const response = await fetch('http://localhost:5000/employee/salary', {
            method: 'POST',
            headers: {
                'Authorization': accessToken,
                'X-User-ID': userId,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody),
            mode: 'cors', // 明確指定為 CORS 模式
            credentials: 'same-origin' // 如需發送 cookies，可改為 'include'
        }).catch(error => {
            console.error('Fetch 錯誤:', error);
            if (error.message.includes('CORS')) {
                throw new Error('CORS 錯誤: 伺服器未允許跨源請求，請檢查伺服器 CORS 配置');
            }
            throw error;
        });
        
        // 檢查回應中的 CORS 標頭
        console.log('回應狀態碼:', response.status);
        console.log('回應 CORS 標頭:', {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        });

        if (!response.ok) {
            throw new Error(`伺服器回應錯誤: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('薪資查詢回應:', JSON.stringify(data));

        // 原有的處理代碼
        if (data.status !== 'success') {
            throw new Error(data.message || '查詢失敗');
        }
        
        // ...其餘代碼保持不變...
    } catch (error) {
        console.error('查詢薪資錯誤:', error);
        salaryInfo.innerHTML = `<div class="error">${error.message}</div>`;
        retryButton.style.display = 'block';
        
        // 為 CORS 錯誤提供更詳細的診斷信息
        if (error.message.includes('CORS')) {
            salaryInfo.innerHTML += `
                <div class="error-details">
                    <p>CORS 錯誤診斷:</p>
                    <ul>
                        <li>請求來源: ${window.location.origin}</li>
                        <li>目標伺服器: http://localhost:5000</li>
                        <li>請確認伺服器已正確配置 CORS，應包含:</li>
                        <li>- Access-Control-Allow-Origin: ${window.location.origin} 或 *</li>
                        <li>- Access-Control-Allow-Methods: POST, OPTIONS</li>
                        <li>- Access-Control-Allow-Headers: Authorization, X-User-ID, Content-Type</li>
                    </ul>
                </div>
            `;
        }
        
        if (error.message.includes('認證已過期')) {
            localStorage.clear();
            console.log('認證已過期，但不會自動跳轉，便於查看錯誤');
            // 註解掉自動跳轉，方便查看錯誤
            // setTimeout(() => {
            //    window.location.href = 'index.html';
            // }, 2000);
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
