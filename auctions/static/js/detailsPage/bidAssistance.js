document.addEventListener('DOMContentLoaded', () => {
    const assistantButton = document.getElementById('assistantButton');
    const assistantModal = document.getElementById('assistantModal');
    const closeModalButton = document.getElementById('closeModalButton');
    const ads = document.getElementById('ads');
    const ass = document.getElementById('ass');
    const getStartedButton = document.getElementById('getStartedButton');

    // Initially hide the assistant section
    ass.classList.add('hidden');

    // Handle "Get Started" button click
    getStartedButton.addEventListener('click', () => {
        ads.classList.add('hidden');
        ass.classList.remove('hidden');
    });

    // Show modal function
    const showModal = () => {
        assistantModal.classList.remove('hidden', 'opacity-0', 'scale-50');
        assistantModal.classList.add('opacity-100', 'scale-100');
    };

    // Hide modal function
    const hideModal = () => {
        assistantModal.classList.add('opacity-0', 'scale-50');
        assistantModal.classList.remove('opacity-100', 'scale-100');
        setTimeout(() => {
            assistantModal.classList.add('hidden');
        }, 300);
    };

    // Show modal after a delay
    setTimeout(showModal, 3000);

    // Toggle modal visibility on button click
    assistantButton.addEventListener('click', () => {
        assistantModal.classList.contains('hidden') ? showModal() : hideModal();
    });

    // Close modal on close button click
    closeModalButton.addEventListener('click', hideModal);
});

// Handle form submission
async function handleSetBidAssistant(event) {
    event.preventDefault();

    const maxBid = document.getElementById('maxBid').value;

    if (!maxBid) {
        alert('Please enter a bid amount.');
        return;
    }

    try {
        const response = await fetch(`/auction/bid_assistant/{{ list.id }}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'), // CSRF token
            },
            body: JSON.stringify({max_bid: parseFloat(maxBid)}),
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message);
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An unexpected error occurred. Please try again later.');
    }
}

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const trimmed = cookie.trim();
            if (trimmed.startsWith(`${name}=`)) {
                cookieValue = decodeURIComponent(trimmed.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
