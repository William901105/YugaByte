/**
 * 員工打卡系統的主要JavaScript文件
 * 
 * 功能說明：
 * 1. 即時顯示當前時間
 * 2. 處理上班打卡（type: 'i'）
 * 3. 處理下班打卡（type: 'o'）
 * 4. 驗證使用者登入狀態
 */

document.addEventListener('DOMContentLoaded', function () {
    // 初始化
    const userId = localStorage.getItem('user_id');
    const accessToken = localStorage.getItem('access_token');

    // 檢查登入狀態
    if (!userId || !accessToken) {
        alert('未登入，請重新登入');
        window.location.href = 'index.html';
        return;
    }

    const clockResultElement = document.getElementById('clockResult');
    const retryButton = document.getElementById('retryButton');
    const timeDisplay = document.getElementById('currentTime');
    let lastClockType = null;

    // 更新目前時間
    function updateTime() {
        timeDisplay.textContent = new Date().toLocaleString();
    }
    updateTime();
    setInterval(updateTime, 1000);    // 驗證 token
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

    // 打卡功能
    async function performClock(type) {
        lastClockType = type;
        const clockButton = type === 'i' ? document.getElementById('clockInButton') : document.getElementById('clockOutButton');
        
        try {
            clockButton.disabled = true;
            clockButton.textContent = '處理中...';
            retryButton.style.display = 'none';

            // 驗證 token
            const isValid = await verifyToken();
            if (!isValid) {
                throw new Error('認證已過期，請重新登入');
            }
              // 呼叫打卡 API
            const currentTime = Math.floor(Date.now() / 1000);
            const requestBody = {
                user_id: userId,
                type: type,
                time: currentTime,
                duration: type === 'i' ? 0 : 28800 // 下班時預設工作8小時
            };
            
            console.log('發送打卡請求 - 方法: POST, URL: /record');
            console.log('請求參數:', JSON.stringify(requestBody));
            
            const response = await fetch('http://localhost:5000/record', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();
            console.log('打卡回應:', JSON.stringify(data));

            if (data.status !== 'success') {
                throw new Error(data.message || '打卡失敗');
            }

            // 打卡成功顯示
            clockResultElement.innerHTML = `
                <div class="success">
                    <strong>打卡成功！</strong><br>
                    ${type === 'i' ? '上班' : '下班'}打卡時間：${new Date().toLocaleString()}
                </div>
            `;
        } catch (error) {
            console.error('打卡錯誤:', error);
            clockResultElement.innerHTML = `
                <div class="error">
                    <strong>打卡失敗</strong><br>
                    ${error.message}
                </div>
            `;
            retryButton.style.display = 'block';
              if (error.message.includes('認證已過期')) {
                localStorage.clear();
                console.log('認證已過期，但不會自動跳轉，便於查看錯誤');
                // 註解掉自動跳轉，方便查看錯誤
                // setTimeout(() => {
                //    window.location.href = 'index.html';
                // }, 2000);
            }
        } finally {
            clockButton.disabled = false;
            clockButton.textContent = type === 'i' ? '上班打卡' : '下班打卡';
        }
    }

    // 上班打卡按鈕
    document.getElementById('clockInButton').addEventListener('click', () => performClock('i'));

    // 下班打卡按鈕
    document.getElementById('clockOutButton').addEventListener('click', () => performClock('o'));

    // 重試按鈕
    retryButton.addEventListener('click', () => {
        if (lastClockType) {
            performClock(lastClockType);
        }
    });

    // 登出按鈕
    document.getElementById('logoutButton').addEventListener('click', () => {
        localStorage.clear();
        window.location.href = 'index.html';
    });
});
