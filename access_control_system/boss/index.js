document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const messageDiv = document.getElementById('message');

    // 檢查是否有錯誤訊息
    const errorMessage = sessionStorage.getItem('error_message');
    if (errorMessage) {
        messageDiv.textContent = errorMessage;
        messageDiv.className = 'message error';
        sessionStorage.removeItem('error_message');
    }

    // 檢查是否已登入
    const token = localStorage.getItem('access_token');
    if (token) {
        window.location.href = 'dashboard.html';
        return;
    }

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const account = document.getElementById('account').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('http://localhost:5000/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    account,
                    password,
                    role: 'boss'
                })
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                // 登入成功，保存所有認證信息
                localStorage.setItem('access_token', data.data.access_token);
                localStorage.setItem('refresh_token', data.data.refresh_token);
                localStorage.setItem('user_id', data.data.user_id);
                
                messageDiv.textContent = '登入成功！正在跳轉...';
                messageDiv.className = 'message success';
                
                // 跳轉到主頁面
                setTimeout(() => {
                    window.location.href = 'dashboard.html';
                }, 1000);
            } else {
                // 登入失敗
                messageDiv.textContent = data.message || '登入失敗，請檢查帳號密碼';
                messageDiv.className = 'message error';
            }
        } catch (error) {
            messageDiv.textContent = '系統錯誤，請稍後再試';
            messageDiv.className = 'message error';
            console.error('Login error:', error);
        }
    });
}); 