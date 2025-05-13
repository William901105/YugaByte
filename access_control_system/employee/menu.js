/**
 * 員工選單頁面的主要JavaScript文件
 * 
 * 功能說明：
 * 1. 驗證使用者登入狀態
 * 2. 顯示個人化歡迎訊息
 * 3. 處理登出功能
 * 4. 整合 MQTT 即時通知系統
 * 5. 處理各類型通知顯示：
 *    - 遲到通知
 *    - 缺席通知
 *    - 加班通知
 * 
 * MQTT 配置：
 * - Broker: broker.hivemq.com:8000
 * - 訂閱主題：employee/{userId}/notifications
 * 
 * 本地儲存：
 * - user_id：使用者ID
 * - access_token：存取權杖
 * 
 * 安全考量：
 * - 檢查登入狀態
 * - 安全登出機制
 * - MQTT 連線加密
 */

document.addEventListener('DOMContentLoaded', function () {
    const userId = localStorage.getItem('user_id');
    const accessToken = localStorage.getItem('access_token');

    if (!userId || !accessToken) {
        alert('未登入，請重新登入');
        window.location.href = 'index.html';
        return;
    }

    document.getElementById('logoutButton').addEventListener('click', function () {
        localStorage.clear();
        alert('已成功登出');
        window.location.href = 'index.html';
    });

    // 顯示使用者名稱
    const welcomeMessage = document.querySelector('h1');
    welcomeMessage.textContent = `歡迎，${userId}`;

    // MQTT 客戶端初始化
    const client = new Paho.MQTT.Client('broker.hivemq.com', 8000, `clientId-${Math.random().toString(16).substr(2, 8)}`);
    
    // 當收到消息時的處理函數
    client.onMessageArrived = function(message) {
        try {
            const payload = JSON.parse(message.payloadString);
            const notificationType = payload.type;
            let notificationText = '';
            
            switch(notificationType) {
                case 'late':
                    notificationText = `您於 ${new Date(payload.time * 1000).toLocaleString()} 遲到了 ${payload.duration} 分鐘`;
                    break;
                case 'absent':
                    notificationText = `您於 ${new Date(payload.time * 1000).toLocaleString()} 被記錄為缺席`;
                    break;
                case 'overtime':
                    notificationText = `您於 ${new Date(payload.time * 1000).toLocaleString()} 加班了 ${payload.duration} 小時`;
                    break;
                default:
                    notificationText = `您收到一則新通知: ${message.payloadString}`;
            }
            
            // 顯示通知
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.innerHTML = `
                <div class="notification-header">
                    <span>${notificationType === 'overtime' ? '加班通知' : '異常通知'}</span>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="notification-body">${notificationText}</div>
            `;
            
            document.body.appendChild(notification);
            
            // 添加關閉按鈕功能
            notification.querySelector('.close-btn').addEventListener('click', function() {
                notification.remove();
            });
            
            // 5秒後自動消失
            setTimeout(() => {
                notification.classList.add('fade-out');
                setTimeout(() => notification.remove(), 500);
            }, 5000);
            
        } catch (e) {
            console.error('無法解析 MQTT 消息:', e);
        }
    };

    // 連線失敗處理
    client.onConnectionLost = function() {
        document.getElementById('mqttStatus').style.display = 'block';
        // 嘗試重新連接
        setTimeout(function() {
            connectMQTT();
        }, 5000);
    };

    // 連線成功處理
    function onConnect() {
        console.log('MQTT 已連線');
        document.getElementById('mqttStatus').style.display = 'none';
        // 訂閱個人通知頻道
        client.subscribe(`employee/${userId}/notification`);
    }

    // 嘗試連接 MQTT
    function connectMQTT() {
        try {
            client.connect({
                onSuccess: onConnect,
                useSSL: true,
                timeout: 3,
                onFailure: function() {
                    document.getElementById('mqttStatus').style.display = 'block';
                    setTimeout(connectMQTT, 5000);
                }
            });
        } catch(e) {
            console.error('MQTT 連線錯誤:', e);
            document.getElementById('mqttStatus').style.display = 'block';
        }
    }

    // 初始嘗試連接
    connectMQTT();
});
