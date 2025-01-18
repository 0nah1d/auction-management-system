const notificationSound = new Audio('/static/mp3/notification.mp3');
const socket = new WebSocket(`ws://localhost:8000/ws/${user_id}/notifications/`);

socket.onopen = function () {
    console.log('WebSocket connect');
};

socket.onmessage = function (event) {
    event = JSON.parse(event.data);
    notificationSound.play().catch(() => console.log());

    const originalTitle = document.title;
    document.title = event.message;

    setTimeout(() => {
        document.title = originalTitle;
    }, 3000);
    get_notifications();
};

socket.onclose = function () {
    console.log('WebSocket disconnect');
};

socket.onerror = function (error) {
    console.error('WebSocket error:', error);
};

const deleteNotificationButton = document.getElementById('delete_notification');

function get_notifications() {
    fetch('/notifications')
        .then(response => response.json())
        .then(data => {
            const notificationList = document.getElementById('notification_list');
            const notificationDot = document.getElementById('notification_dot');
            let hasUnread = false;

            notificationList.innerHTML = '';

            if (data.notifications.length === 0) {
                const emptyMessage = document.createElement('p');
                emptyMessage.className = 'text-gray-500 text-center p-4';
                emptyMessage.textContent = 'No notifications available.';
                notificationList.appendChild(emptyMessage);

                // Hide the notification dot
                notificationDot.classList.add('hidden');

                // Disable the delete notification button when no notifications are available
                deleteNotificationButton.disabled = true;
                deleteNotificationButton.classList.remove('hover:underline');
                return;
            }

            data.notifications.forEach(notification => {
                const li = document.createElement('li');
                const hr = document.createElement('hr');
                li.className = `${notification.is_read === false ? 'bg-gray-200' : 'bg-white'} p-4 cursor-pointer hover:bg-gray-200`;
                li.innerHTML = `
                    <p class="text-gray-800 font-medium">${notification.message}</p>
                    <small class="text-gray-500 text-xs" data-timestamp="${notification.created_at}"></small>
                `;
                notificationList.appendChild(li);
                hr.className = 'border-gray-400';
                notificationList.appendChild(hr);

                if (!notification.is_read) {
                    hasUnread = true;
                }

                li.onclick = function () {
                    fetch(`/notifications/read/${notification.id}`)
                        .then(response => response.json())
                        .then(data => {
                            get_notifications();
                        });
                };
            });

            if (hasUnread) {
                notificationDot.classList.remove('hidden');
            } else {
                notificationDot.classList.add('hidden');
            }

            deleteNotificationButton.disabled = false;

            const timeElements = document.querySelectorAll('[data-timestamp]');
            timeElements.forEach(element => {
                const timestamp = element.getAttribute('data-timestamp');
                element.textContent = moment(new Date(timestamp)).fromNow();
            });

        })
        .catch(error => {
            console.error('Error fetching notifications:', error);
        });
}

get_notifications();

deleteNotificationButton.onclick = function () {
    deleteNotificationButton.innerHTML = '<span class="animate-spin mr-2 w-4 h-4 border-t-2 border-b-2 border-gray-500 border-solid rounded-full"></span> Deleting...';
    deleteNotificationButton.disabled = true;

    fetch(`/notifications/delete_all`)
        .then(response => response.json())
        .then(data => {
            get_notifications();
            deleteNotificationButton.innerHTML = 'Delete All';
            deleteNotificationButton.disabled = false;
        })
        .catch(error => {
            console.error('Error deleting notifications:', error);
            deleteNotificationButton.innerHTML = 'Delete All';
            deleteNotificationButton.disabled = false;
        });
};
