// 1. Set Database Lokal Browser untuk Admin & Warga Bawaan
if (!localStorage.getItem('users')) {
    const defaultUsers = [
        { username: 'admin', password: 'admin123', role: 'admin' },
        { username: 'wawan', password: 'wawan123', role: 'warga' }
    ];
    localStorage.setItem('users', JSON.stringify(defaultUsers));
}

// 2. Aksi Pindah Form Tampilan (Login <-> Daftar)
document.getElementById('link-ke-daftar')?.addEventListener('click', function(e) {
    e.preventDefault();
    document.getElementById('login-box').classList.add('d-none');
    document.getElementById('register-box').classList.remove('d-none');
});

document.getElementById('link-ke-login')?.addEventListener('click', function(e) {
    e.preventDefault();
    document.getElementById('register-box').classList.add('d-none');
    document.getElementById('login-box').classList.remove('d-none');
});

// 3. Sistem Pendaftaran Akun Warga Baru
document.getElementById('btn-register')?.addEventListener('click', function() {
    const nama = document.getElementById('reg-nama').value.trim();
    const username = document.getElementById('reg-username').value.trim();
    const password = document.getElementById('reg-password').value.trim();

    if (!nama || !username || !password) {
        alert('Semua kolom pendaftaran wajib diisi!');
        return;
    }

    let currentUsers = JSON.parse(localStorage.getItem('users')) || [];
    
    // Cek duplikasi username
    const userExists = currentUsers.find(u => u.username === username);
    if (userExists) {
        alert('Username sudah terdaftar! Pilih username lain.');
        return;
    }

    // Simpan data pendaftar baru
    currentUsers.push({ username: username, password: password, role: 'warga' });
    localStorage.setItem('users', JSON.stringify(currentUsers));

    alert('Pendaftaran Berhasil! Silakan masuk dengan akun baru Anda.');
    document.getElementById('register-box').classList.add('d-none');
    document.getElementById('login-box').classList.remove('d-none');
});

// 4. Sistem Verifikasi Kredensial Login
document.getElementById('btn-login')?.addEventListener('click', function() {
    const inputUser = document.getElementById('login-username').value.trim();
    const inputPass = document.getElementById('login-password').value.trim();

    const currentUsers = JSON.parse(localStorage.getItem('users')) || [];
    const validUser = currentUsers.find(u => u.username === inputUser && u.password === inputPass);

    if (validUser) {
        alert(`Login Sukses! Selamat datang, ${validUser.username}.`);
        
        // Sembunyikan form login & arahkan langsung ke dashboard SPA
        document.getElementById('auth-container').classList.add('d-none');
        window.location.hash = '#dashboard';
        
        // Memaksa reload/trigger router jika diperlukan browser
        if(typeof router === 'function') { router(); }
    } else {
        alert('Kombinasi password atau username salah!');
    }
});