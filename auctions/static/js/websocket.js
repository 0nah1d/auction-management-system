const socket = new WebSocket('ws://localhost:8000/ws/1/notifications/');

socket.onopen = function () {
    console.log('WebSocket connect');
};

socket.onmessage = function (event) {
    console.log('Server Message:', event.data);
};

socket.onclose = function () {
    console.log('WebSocket disconnect');
};

socket.onerror = function (error) {
    console.error('WebSocket error:', error);
};
