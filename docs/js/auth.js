function setupLoginForm() {
    const form = document.getElementById('loginForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault(); // Mencegah reload kebocoran credentials (Lab 11)
        
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        const result = await requestAPI('/token/', 'POST', { username, password });

        if (result && result.status === 200) {
            localStorage.setItem('access_token', result.data.access);
            localStorage.setItem('refresh_token', result.data.refresh);
            window.location.hash = '#dashboard';
        } else {
            alert('Kombinasi password atau username salah!');
        }
    });
}

function logout() {
    localStorage.clear();
    window.location.hash = '#login';
}