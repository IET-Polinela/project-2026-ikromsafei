const BASE_URL = "http://103.151.63.87:8008/api/";

async function requestAPI(endpoint, method = 'GET', bodyData = null) {
    const url = `${BASE_URL}${endpoint}`;
    const token = localStorage.getItem('access_token');
    
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = { method: method, headers: headers };
    if (bodyData && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        config.body = JSON.stringify(bodyData);
    }

    try {
        const response = await fetch(url, config);
        
        if (response.status === 401 && localStorage.getItem('refresh_token')) {
            const refreshSuccess = await handleTokenRefresh();
            if (refreshSuccess) return await requestAPI(endpoint, method, bodyData);
        }
        
        if (response.status === 204) return { status: 204 };
        const data = await response.json();
        return { status: response.status, data: data };
    } catch (error) {
        console.error("Gagal melakukan permintaan API:", error);
        return null;
    }
}

async function handleTokenRefresh() {
    const refresh = localStorage.getItem('refresh_token');
    const response = await fetch(`${BASE_URL}/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refresh })
    });
    
    if (response.ok) {
        const resData = await response.json();
        localStorage.setItem('access_token', resData.access);
        return true;
    } else {
        logout();
        return false;
    }
}