const socket = new WebSocket('ws://localhost:8000/ws/1/notifications/');

socket.onopen = function () {
    console.log('WebSocket connect');
};

socket.onmessage = function (event) {
    console.log('Server Message:', event);

};

socket.onclose = function () {
    console.log('WebSocket disconnect');
};

socket.onerror = function (error) {
    console.error('WebSocket error:', error);
};


function get_notifications() {
    fetch('/notifications')
        .then(response => response.json())
        .then(data => {
            console.log(data.notifications)
            const notificationList = document.getElementById('notification_list');
            notificationList.innerHTML = '';

            data.notifications.forEach(notification => {
                const li = document.createElement('li');
                const hr = document.createElement('hr');
                li.className = `${notification.is_read === false ? 'bg-gray-200' : 'bg-white'} p-4 cursor-pointer hover:bg-gray-200`;
                li.innerHTML = `
                              <p class="text-gray-800 font-medium">${notification.message}</p>
                              <small class="text-gray-500 text-xs">${notification.created_at}</small>
                            `;
                notificationList.appendChild(li);
                hr.className = 'border-gray-400';
                notificationList.appendChild(hr);
            });
        })
}

get_notifications()