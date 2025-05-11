document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('registerForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const togglePasswordButton = document.querySelector('.toggle-password');
    const button = document.querySelector('.login-button');

    // 密碼切換顯示
    togglePasswordButton.addEventListener('click', function () {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
    });

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();

        if (!email || !password) {
            alert('請填寫所有欄位');
            return;
        }

        // 通知使用者處理中
        button.disabled = true;
        button.textContent = '註冊中...';

        try {
            // 呼叫 employee_api 註冊
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
