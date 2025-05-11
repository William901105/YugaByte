document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const togglePasswordButton = document.querySelector('.toggle-password');
    const loginButton = document.querySelector('.login-button');
    
    // 為了更好的用戶體驗，設置 placeholder
    emailInput.setAttribute('placeholder', ' ');
    passwordInput.setAttribute('placeholder', ' ');

    // 切換密碼顯示/隱藏
    togglePasswordButton.addEventListener('click', function() {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        
        // 更新圖標
        if (type === 'text') {
            this.style.backgroundImage = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411M21 21l-3.59-3.59'%3E%3C/path%3E%3C/svg%3E")`;
        } else {
            this.style.backgroundImage = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M15 12a3 3 0 11-6 0 3 3 0 016 0z' /%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z' /%3E%3C/svg%3E")`;
        }
    });

    // 表單提交處理
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 簡單驗證
        const email = emailInput.value;
        const password = passwordInput.value;
        const remember = document.getElementById('remember').checked;
        
        if (!email || !password) {
            alert('請填寫所有必填欄位');
            return;
        }
        

        // 模擬登入處理
        loginButton.disabled = true;
        loginButton.textContent = '登入中...';
        
        // 這裡通常會發送API請求
        setTimeout(() => {
            console.log('登入資料:', { email, remember });
            alert('登入成功！');
            loginButton.disabled = false;
            loginButton.textContent = '登入';
        }, 1500);
    });
});
