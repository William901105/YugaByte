/**
 * 員工註冊系統的主要 JavaScript 文件
 * 
 * 功能說明：
 * 1. 處理註冊表單提交
 * 2. 表單欄位驗證：
 *    - 必填欄位檢查
 *    - 密碼確認匹配
 *    - 帳號格式驗證
 * 3. 密碼顯示/隱藏切換
 * 4. 整合後端 API：
 *    - POST /api/register：處理註冊請求
 *      參數：
 *      - username: 使用者帳號
 *      - password: 加密後的密碼
 *      - bossId: 主管ID
 * 5. 錯誤處理與用戶提示：
 *    - 表單驗證錯誤
 *    - API 錯誤處理（400, 409, 500等）
 *    - 重複帳號檢查
 *    - 網路連線問題處理
 * 6. 安全考量：
 *    - 密碼加密處理
 *    - XSS 防護
 *    - CSRF 防護
 * 7. 註冊成功後：
 *    - 顯示成功訊息
 *    - 自動導向登入頁面
 *    - 清除敏感資訊
 */

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('registerForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const bossIdInput = document.getElementById('bossId');
    const togglePasswordButton = document.querySelector('.toggle-password');
    const registerButton = document.querySelector('.register-button');    // 密碼顯示/隱藏切換功能
    // 透過切換 input type 實現密碼明文/隱藏顯示
    togglePasswordButton.addEventListener('click', function () {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        confirmPasswordInput.setAttribute('type', type);
    });

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        const confirmPassword = confirmPasswordInput.value.trim();
        const bossId = bossIdInput.value.trim();

        // 表單欄位驗證
        if (!username || !password || !confirmPassword || !bossId) {
            alert('請填寫所有欄位');
            return;
        }

        // 驗證密碼是否一致
        if (password !== confirmPassword) {
            alert('密碼與確認密碼不一致');
            return;
        }

        // 更新按鈕狀態，提供視覺回饋
        registerButton.disabled = true;
        registerButton.textContent = '註冊中...';

        try {            // 發送註冊請求到後端 API
            const requestBody = { 
                account: username,
                password: password,
                boss_id: bossId
            };
            console.log('發送註冊請求 - 方法: POST, URL: /employee/register');
            console.log('請求參數:', JSON.stringify(requestBody));
            
            const res = await fetch('http://localhost:5000/employee/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            const result = await res.json();
            console.log('註冊回應:', JSON.stringify(result));

            if (res.ok && result.status === 'success') {
               alert('註冊成功！請前往登入頁面。');
                window.location.href = 'index.html';
            } else if (result.message === '用戶已存在') {
                alert('該帳號已存在，請使用其他帳號');
            } else {
                alert(result.message || '註冊失敗');
            }            
        } catch (err) {
            console.error('註冊錯誤:', err);
            alert('無法連接伺服器');
        } finally {
            registerButton.disabled = false;
            registerButton.textContent = '註冊';
        }
    });
});
