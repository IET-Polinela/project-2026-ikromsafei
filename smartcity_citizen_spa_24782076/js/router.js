const routes = {
    '#login': `
        <div class="row justify-content-center mt-5">
            <div class="col-md-4">
                <div class="card shadow-sm border-0 p-4">
                    <h4 class="text-center fw-bold mb-4">Login Portal Warga</h4>
                    <form id="loginForm">
                        <div class="mb-3"><input type="text" id="loginUsername" class="form-control" placeholder="Username" required></div>
                        <div class="mb-3"><input type="password" id="loginPassword" class="form-control" placeholder="Password" required></div>
                        <button type="submit" class="btn btn-primary w-100 fw-bold">Masuk</button>
                    </form>
                </div>
            </div>
        </div>
    `,
    '#dashboard': `
        <div class="row g-4">
            <aside class="col-12 col-lg-3">
                <div class="card border-0 p-3 shadow-sm mb-3">
                    <button class="btn btn-primary btn-lg w-100 fw-bold mb-3" onclick="openCreateModal()"><i class="bi bi-plus-circle-fill me-2"></i>Laporan Baru</button>
                    <hr>
                    <h6 class="fw-bold mb-3"><i class="bi bi-pie-chart-fill me-2 text-primary"></i>Rekap Status Saya</h6>
                    <div class="list-group list-group-flush" id="sidebarStats">
                        <div class="d-flex justify-content-between mb-2"><span>Draft</span><span class="badge bg-secondary rounded-pill" id="statDraft">0</span></div>
                        <div class="d-flex justify-content-between mb-2"><span>Diajukan</span><span class="badge bg-primary rounded-pill" id="statReported">0</span></div>
                        <div class="d-flex justify-content-between mb-2"><span>Diproses</span><span class="badge bg-warning text-dark rounded-pill" id="statProgress">0</span></div>
                        <div class="d-flex justify-content-between mb-2"><span>Selesai</span><span class="badge bg-success rounded-pill" id="statResolved">0</span></div>
                    </div>
                </div>
                <button class="btn btn-outline-danger w-100 fw-bold" onclick="logout()"><i class="bi bi-box-arrow-right me-2"></i>Keluar</button>
            </aside>
            <section class="col-12 col-lg-9">
                <ul class="nav nav-tabs mb-3" id="dashboardTabs">
                    <li class="nav-item"><button class="nav-link active fw-bold" onclick="switchTab('my_reports')">Laporan Saya</button></li>
                    <li class="nav-item"><button class="nav-link fw-bold" onclick="switchTab('feed')">Feed Kota</button></li>
                </ul>
                <div id="listContainer" class="row row-cols-1 row-cols-md-2 g-3"></div>
                <nav class="mt-4"><ul class="pagination justify-content-center" id="paginationContainer"></ul></nav>
            </section>
        </div>
    `
};

function handleRouting() {
    const hash = window.location.hash || '#login';
    const appContent = document.getElementById('app-content');
    if (!appContent) return;
    
    if (hash === '#dashboard' && !localStorage.getItem('access_token')) { window.location.hash = '#login'; return; }
    if (hash === '#login' && localStorage.getItem('access_token')) { window.location.hash = '#dashboard'; return; }

    appContent.innerHTML = routes[hash] || '<h3>Halaman Tidak Tersedia</h3>';
    if (hash === '#login') setupLoginForm();
    if (hash === '#dashboard') initDashboard();
}

window.addEventListener('hashchange', handleRouting);
window.addEventListener('DOMContentLoaded', handleRouting);