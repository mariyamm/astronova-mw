/* Authentication helper functions */

// Check if user is authenticated
function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

// Fetch with authentication token
async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        window.location.href = '/login.html';
        throw new Error('No authentication token');
    }

    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };

    const response = await fetch(url, {
        ...options,
        headers
    });

    // If unauthorized, redirect to login
    if (response.status === 401) {
        localStorage.removeItem('access_token');
        window.location.href = '/login.html';
    }

    return response;
}

// Logout function
function logout() {
    if (confirm('Сигурни ли сте, че искате да излезете?')) {
        localStorage.removeItem('access_token');
        window.location.href = '/login.html';
    }
}
