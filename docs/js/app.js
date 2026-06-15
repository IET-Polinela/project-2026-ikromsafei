let currentTab = 'my_reports';
let currentPage = 1;
let allReports = [];
let editingReportId = null;
let bsModal = null;

function initDashboard() {
    currentTab = 'my_reports';
    currentPage = 1;
    
    // Inisialisasi object Bootstrap Modal secara aman tanpa mengikat tombol manual
    const modalElement = document.getElementById('reportModal');
    if (modalElement && typeof bootstrap !== 'undefined') {
        bsModal = new bootstrap.Modal(modalElement);
    }
    
    // Tarik list data terpaginasi dari server backend DRF
    loadDashboardData(currentTab, currentPage);
}

function switchTab(tabName) {
    currentTab = tabName;
    currentPage = 1;
    
    const buttons = document.querySelectorAll('#dashboardTabs .nav-link');
    if (buttons.length >= 2) {
        buttons[0].classList.toggle('active', tabName === 'my_reports');
        buttons[1].classList.toggle('active', tabName === 'feed');
    }
    
    loadDashboardData(currentTab, currentPage);
}

async function loadDashboardData(tab, page) {
    currentTab = tab;
    currentPage = page;

    const result = await requestAPI(`/report/?tab=${tab}&page=${page}`, 'GET');
    const container = document.getElementById('listContainer');
    
    if (result && result.status === 200) {
        allReports = result.data.results || [];
        renderList(allReports);
        renderPagination(result.data.count);
        loadSummaryStats(); 
    } else {
        if (container) {
            container.innerHTML = `
                <div class="col-12 text-center text-muted p-5">
                    <i class="bi bi-exclamation-triangle fs-1 text-danger"></i>
                    <p class="mt-2 fw-bold">Gagal memuat list data dari backend server.</p>
                </div>
            `;
        }
    }
}

function renderList(reports) {
    const container = document.getElementById('listContainer');
    if (!container) return;
    container.innerHTML = '';

    if (reports.length === 0) {
        container.innerHTML = '<div class="col-12 text-muted p-3 fw-medium">Belum ada laporan yang tersedia di tab ini.</div>';
        return;
    }

    reports.forEach(report => {
        let badgeColor = 'bg-secondary';
        let progressWidth = '10%';
        
        if (report.status === 'REPORTED') { badgeColor = 'bg-primary'; progressWidth = '35%'; }
        if (report.status === 'VERIFIED') { badgeColor = 'bg-info text-dark'; progressWidth = '55%'; }
        if (report.status === 'IN_PROGRESS') { badgeColor = 'bg-warning text-dark'; progressWidth = '75%'; }
        if (report.status === 'RESOLVED') { badgeColor = 'bg-success'; progressWidth = '100%'; }

        const showEditBtn = report.is_owner && report.status === 'DRAFT';

        const card = document.createElement('div');
        card.className = 'col';
        card.innerHTML = `
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="fw-bold m-0 text-dark">${report.title}</h6>
                        <span class="badge ${badgeColor}">${report.status}</span>
                    </div>
                    <p class="small text-muted mb-2"><i class="bi bi-geo-alt-fill me-1 text-danger"></i>${report.location}</p>
                    <p class="text-secondary small mb-3">${report.description}</p>
                    
                    <div class="progress mb-3" style="height: 6px;">
                        <div class="progress-bar" role="progressbar" style="width: ${progressWidth}"></div>
                    </div>
                    
                    <div class="d-flex justify-content-between align-items-center mt-2">
                        <span class="text-muted small">Oleh: <b>${report.reporter}</b></span>
                        ${showEditBtn ? `<button class="btn btn-sm btn-primary fw-bold" onclick="openEditModal(${report.id})"><i class="bi bi-pencil-square me-1"></i>Edit Draft</button>` : ''}
                    </div>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

function renderPagination(totalCount) {
    const container = document.getElementById('paginationContainer');
    if (!container) return;
    container.innerHTML = '';
    
    const totalPages = Math.ceil(totalCount / 10);
    if (totalPages <= 1) return;

    for (let i = 1; i <= totalPages; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === currentPage ? 'active' : ''}`;
        li.innerHTML = `<button class="page-link fw-bold">${i}</button>`;
        li.onclick = () => loadDashboardData(currentTab, i);
        container.appendChild(li);
    }
}

async function loadSummaryStats() {
    const result = await requestAPI('/report/?page_size=1000', 'GET');
    if (result && result.status === 200) {
        const dataArr = result.data.results || [];
        
        const elDraft = document.getElementById('statDraft');
        const elReported = document.getElementById('statReported');
        const elProgress = document.getElementById('statProgress');
        const elResolved = document.getElementById('statResolved');

        if (elDraft) elDraft.innerText = dataArr.filter(r => r.status === 'DRAFT').length;
        if (elReported) elReported.innerText = dataArr.filter(r => r.status === 'REPORTED').length;
        if (elProgress) elProgress.innerText = dataArr.filter(r => r.status === 'IN_PROGRESS').length;
        if (elResolved) elResolved.innerText = dataArr.filter(r => r.status === 'RESOLVED').length;
    }
}

function openCreateModal() {
    editingReportId = null;
    const form = document.getElementById('reportForm');
    if (form) form.reset();
    
    document.getElementById('reportModalLabel').innerText = 'Buat Laporan Baru';
    if (bsModal) bsModal.show();
}

function openEditModal(id) {
    editingReportId = id;
    const report = allReports.find(r => r.id === id);
    if (!report) return;

    document.getElementById('formTitle').value = report.title;
    document.getElementById('formCategory').value = report.category;
    document.getElementById('formLocation').value = report.location;
    document.getElementById('formDescription').value = report.description;

    document.getElementById('reportModalLabel').innerText = 'Edit Draft Laporan';
    if (bsModal) bsModal.show();
}

async function submitForm(targetStatus) {
    const titleVal = document.getElementById('formTitle') ? document.getElementById('formTitle').value.trim() : '';
    const categoryVal = document.getElementById('formCategory') ? document.getElementById('formCategory').value : '';
    const locationVal = document.getElementById('formLocation') ? document.getElementById('formLocation').value.trim() : '';
    const descriptionVal = document.getElementById('formDescription') ? document.getElementById('formDescription').value.trim() : '';

    if (!titleVal || !locationVal || !descriptionVal) {
        alert('Mohon lengkapi semua bidang form data sebelum mengirim!');
        return;
    }

    const payload = {
        title: titleVal,
        category: categoryVal,
        location: locationVal,
        description: descriptionVal,
        status: targetStatus
    };

    let result;
    if (editingReportId === null) {
        result = await requestAPI('/report/', 'POST', payload);
    } else {
        result = await requestAPI(`/report/${editingReportId}/`, 'PUT', payload);
    }

    if (result && (result.status === 201 || result.status === 200)) {
        alert(`Sukses menyimpan data laporan sebagai ${targetStatus}!`);
        if (bsModal) bsModal.hide();
        
        const formElement = document.getElementById('reportForm');
        if (formElement) formElement.reset();
        
        editingReportId = null;
        loadDashboardData(currentTab, currentPage); 
    } else {
        alert('Gagal memproses data! Pastikan backend Django Anda sudah menyala.');
    }
}