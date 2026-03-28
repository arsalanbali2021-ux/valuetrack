/**
 * ValueTrack — Loans Page Logic
 * Create loans and view EMI amortization schedules.
 */

document.addEventListener('DOMContentLoaded', () => {
    const user = requireAuth();
    if (!user) return;

    // Update user name in header
    const userNameEl = document.getElementById('userName');
    if (userNameEl) userNameEl.textContent = user.name;

    // Show admin link if admin
    if (user.role === 'admin') {
        const adminLink = document.getElementById('adminLink');
        if (adminLink) adminLink.style.display = '';
    }

    const loanForm = document.getElementById('loanForm');
    const loanAlert = document.getElementById('loanAlert');
    const scheduleSection = document.getElementById('scheduleSection');
    const scheduleBody = document.getElementById('scheduleBody');
    const loanSummary = document.getElementById('loanSummary');
    const paginationContainer = document.getElementById('pagination');

    let currentSchedule = [];
    let currentPage = 1;
    const rowsPerPage = 12;

    // Loan form submission
    loanForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = loanForm.querySelector('button[type="submit"]');

        const principal = parseFloat(document.getElementById('principal').value);
        const rate = parseFloat(document.getElementById('interestRate').value);
        const tenure = parseInt(document.getElementById('tenure').value);
        const startDate = document.getElementById('startDate').value;

        // Validation
        if (!principal || principal <= 0) {
            showAlert(loanAlert, 'Principal must be a positive number.', 'danger');
            return;
        }
        if (rate < 0) {
            showAlert(loanAlert, 'Interest rate cannot be negative.', 'danger');
            return;
        }
        if (!tenure || tenure <= 0) {
            showAlert(loanAlert, 'Tenure must be a positive integer.', 'danger');
            return;
        }
        if (!startDate) {
            showAlert(loanAlert, 'Please select a start date.', 'danger');
            return;
        }

        showLoading(btn);
        try {
            const result = await LoansAPI.create(user.user_id, principal, rate, tenure, startDate);
            showAlert(loanAlert,
                `Loan created! ID: ${result.loan_id}, Monthly EMI: ₹${result.emi.toFixed(2)}`,
                'success');

            // Show summary
            loanSummary.innerHTML = `
                <div class="stat-card card">
                    <div class="stat-label">Loan ID</div>
                    <div class="stat-value">#${result.loan_id}</div>
                </div>
                <div class="stat-card card">
                    <div class="stat-label">Monthly EMI</div>
                    <div class="stat-value">₹${result.emi.toFixed(2)}</div>
                </div>
                <div class="stat-card card">
                    <div class="stat-label">Total Payable</div>
                    <div class="stat-value">₹${(result.emi * tenure).toFixed(2)}</div>
                </div>
            `;
            loanSummary.style.display = 'grid';
            loanSummary.style.gridTemplateColumns = 'repeat(auto-fit, minmax(180px, 1fr))';
            loanSummary.style.gap = '1rem';
            loanSummary.style.marginBottom = '1.5rem';

            // Load schedule
            await loadSchedule(result.loan_id);
        } catch (error) {
            showAlert(loanAlert, error.message, 'danger');
        } finally {
            hideLoading(btn);
        }
    });



    async function loadSchedule(loanId) {
        try {
            const result = await LoansAPI.getSchedule(loanId);
            currentSchedule = result.schedule;
            


            currentPage = 1;
            scheduleSection.classList.remove('hidden');
            renderPage();
        } catch (error) {
            showAlert(loanAlert, `Failed to load schedule: ${error.message}`, 'danger');
        }
    }



    function renderPage() {
        const start = (currentPage - 1) * rowsPerPage;
        const end = start + rowsPerPage;
        const pageData = currentSchedule.slice(start, end);

        scheduleBody.innerHTML = pageData.map(row => `
            <tr>
                <td>${row.month_no}</td>
                <td>₹${row.emi_amount.toFixed(2)}</td>
                <td>₹${row.principal_component.toFixed(2)}</td>
                <td>₹${row.interest_component.toFixed(2)}</td>
                <td>₹${row.remaining_balance.toFixed(2)}</td>
                <td>${row.due_date}</td>
            </tr>
        `).join('');

        renderPagination();
    }

    function renderPagination() {
        const totalPages = Math.ceil(currentSchedule.length / rowsPerPage);
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let html = `<button ${currentPage === 1 ? 'disabled' : ''} onclick="goToPage(${currentPage - 1})">← Prev</button>`;

        for (let i = 1; i <= totalPages; i++) {
            html += `<button class="${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
        }

        html += `<button ${currentPage === totalPages ? 'disabled' : ''} onclick="goToPage(${currentPage + 1})">Next →</button>`;
        paginationContainer.innerHTML = html;
    }

    // Make goToPage globally accessible
    window.goToPage = function (page) {
        currentPage = page;
        renderPage();
    };
});
