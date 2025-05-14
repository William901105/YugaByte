/**
 * 員工打卡系統的主要JavaScript文件
 * 
 * 功能說明：
 * 1. 即時顯示當前時間
 * 2. 處理上班打卡（type: 'i'）
 * 3. 處理下班打卡（type: 'o'）
 * 4. 驗證使用者登入狀態
 * 5. 處理打卡失敗的重試機制
 * 6. 顯示打卡結果和錯誤訊息
 * 
 * API端點：
 * - POST /employee/clock：處理打卡請求
 *   參數：
 *   - type: 'i' (上班) 或 'o' (下班)
 *   標頭：
 *   - Authorization: access_token
 *   - X-User-ID: user_id
 * 
 * 安全機制：
 * - 檢查 localStorage 中的 token
 * - 自動處理 token 過期
 * - 異常處理和錯誤重試
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
    setInterval(updateTime, 1000);

    // 打卡功能
    async function performClock(type) {
        lastClockType = type;
        const clockButton = type === 'i' ? document.getElementById('clockInButton') : document.getElementById('clockOutButton');
        
        try {
            clockButton.disabled = true;
            clockButton.textContent = '處理中...';
            retryButton.style.display = 'none';
            
            // 呼叫打卡 API
            const response = await fetch('http://localhost:5000/employee/clock', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': accessToken,
                    'X-User-ID': userId
                },
                body: JSON.stringify({
                    type: type,
                })
            });

            const data = await response.json();

            if (!response.ok) {
                // Token 過期處理
                if (response.status === 401) {
                    const refreshToken = localStorage.getItem('refresh_token');
                    const refreshResponse = await fetch('http://localhost:5000/authorization/refreshToken', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            refresh_token: refreshToken,
                            user_id: userId
                        })
                    });

                    if (refreshResponse.ok) {
                        const refreshData = await refreshResponse.json();
                        localStorage.setItem('access_token', refreshData.new_access_token);
                        localStorage.setItem('refresh_token', refreshData.new_refresh_token);
                        // 重試打卡
                        clockButton.disabled = false;
                        clockButton.textContent = type === 'i' ? '上班打卡' : '下班打卡';
                        performClock(type);
                        return;
                    } else {
                        throw new Error('認證已過期，請重新登入');
                    }
                }
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
            
            // 如果是認證過期，轉到登入頁
            if (error.message.includes('認證已過期')) {
                localStorage.clear();
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 2000);
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
