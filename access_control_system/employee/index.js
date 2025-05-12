document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');  // 尚未使用，但可搭配驗證
    const togglePasswordButton = document.querySelector('.toggle-password');
    const loginButton = document.querySelector('.login-button');

    // 密碼切換顯示
    togglePasswordButton.addEventListener('click', function () {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
    });

    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim(); // optional，目前API未驗證密碼

if (!email) {
    alert('請輸入帳號');
    return;
}

        loginButton.disabled = true;
        loginButton.textContent = '登入中...';

        try {
            // 1. 呼叫 employee_api 登入，取得 token
            const loginRes = await fetch('http://localhost:5000/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: email })
            });

            const loginData = await loginRes.json();

            if (!loginRes.ok || loginData.status !== 'success') {
                throw new Error(loginData.message || '登入失敗');
            }

            const accessToken = loginData.data.access_token;
            const refreshToken = loginData.data.refresh_token;

            // 2. 呼叫 authorization_api 驗證 token 是否有效
            const authRes = await fetch(`http://localhost:5000/authorization/authorize?access_token=${accessToken}&user_id=${email}`, {
                method: 'GET'
            });

            const authResult = await authRes.json();

            if (!authRes.ok || authResult.result !== 'Valid') {
                throw new Error(authResult.result || 'Token 驗證失敗');
            }

            // 3. 儲存登入資訊
            localStorage.setItem('user_id', email);
            localStorage.setItem('access_token', accessToken);
            localStorage.setItem('refresh_token', refreshToken);

            alert('登入成功！');
            window.location.href = './menu.html'; // 導向功能選單頁面
        } catch (err) {
            // 清理 LocalStorage，避免殘留舊的登入資訊
            localStorage.clear();
            alert(`登入失敗：${err.message}`);
            console.error(err);
        } finally {
            loginButton.disabled = false;
            loginButton.textContent = '登入';
        }
    });
});
