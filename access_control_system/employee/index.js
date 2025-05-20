/**
 * 員工登入頁面的主要JavaScript文件
 * 
 * 功能說明：
 * 1. 處理員工登入表單提交
 * 2. 實現密碼顯示/隱藏切換
 * 3. 與後端API進行身份驗證
 * 4. 處理登入成功後的token儲存和頁面跳轉
 * 
 * API端點：
 * - POST /api/login：員工登入驗證
 * 
 * 本地儲存：
 * - localStorage.setItem('access_token')：儲存登入token
 * - localStorage.setItem('user_id')：儲存用戶ID
 */

document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('loginForm');
    const userIdInput = document.getElementById('userId');
    const passwordInput = document.getElementById('password'); 
    const togglePasswordButton = document.querySelector('.toggle-password');
    const loginButton = document.querySelector('.login-button');

    // 密碼切換顯示
    togglePasswordButton.addEventListener('click', function () {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
    });

    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const userId = userIdInput.value.trim();
        const password = passwordInput.value.trim();

        if (!userId) {
            alert('請輸入帳號');
            return;
        }

        if (!password) {
            alert('請輸入密碼');
            return;
        }

        loginButton.disabled = true;
        loginButton.textContent = '登入中...';

        try {            // 呼叫登入 API
            const response = await fetch('http://localhost:5000/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    account: userId,
                    password: password,
                    role: 'employee' 
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || '登入失敗');
            }

            const data = await response.json();

            if (data.status !== 'success') {
                throw new Error(data.message || '登入失敗');
            }

            // 儲存登入資訊
            localStorage.setItem('user_id', userId);
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            localStorage.setItem('role', 'employee');

            alert('登入成功！');
            window.location.href = './menu.html'; // 導向功能選單頁面
        } catch (err) {
            // 清理 LocalStorage，避免殘留舊的登入資訊
            localStorage.removeItem('user_id');
            
            if (err.message === 'Failed to fetch') {
                alert('無法連線到伺服器，請確認網路或稍後再試');
            } else {
                alert(`登入失敗：${err.message}`);
            }
            console.error(err);
        } finally {
            loginButton.disabled = false;
            loginButton.textContent = '登入';
        }
    });
});
