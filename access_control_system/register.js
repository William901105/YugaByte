/**
 * 註冊頁面的主要 JavaScript 功能
 * 
 * 功能列表：
 * 1. 處理註冊表單提交
 * 2. 表單欄位驗證
 * 3. 密碼顯示/隱藏切換
 * 4. 整合後端 API 進行註冊
 * 5. 錯誤處理與用戶提示
 *    - 表單驗證錯誤
 *    - API 錯誤處理
 *    - 重複帳號檢查
 * 6. 註冊成功後自動導向登入頁面
 */

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('registerForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const togglePasswordButton = document.querySelector('.toggle-password');
    const button = document.querySelector('.login-button');

    // 密碼顯示/隱藏切換功能
    // 透過切換 input type 實現密碼明文/隱藏顯示
    togglePasswordButton.addEventListener('click', function () {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
    });

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();

        // 表單欄位驗證
        if (!email || !password) {
            alert('請填寫所有欄位');
            return;
        }

        // 更新按鈕狀態，提供視覺回饋
        button.disabled = true;
        button.textContent = '註冊中...';

        try {
            // 發送註冊請求到後端 API
            const res = await fetch('http://localhost:5000/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: email }) // password 暫不寫入 DB
            });

            const result = await res.json();

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
            button.disabled = false;
            button.textContent = '註冊';
        }
    });
});
