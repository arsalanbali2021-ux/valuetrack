/**
 * ValueTrack — Expenses Page Logic
 * Manual add, file import, and expense listing.
 */

document.addEventListener('DOMContentLoaded', () => {
    const user = requireAuth();
    if (!user) return;

    const userNameEl = document.getElementById('userName');
    if (userNameEl) userNameEl.textContent = user.name;

    // ---- Manual Add ----
    const expenseForm = document.getElementById('expenseForm');
    const expenseAlert = document.getElementById('expenseAlert');

    expenseForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = expenseForm.querySelector('button[type="submit"]');

        const category = document.getElementById('category').value.trim();
        const amount = parseFloat(document.getElementById('amount').value);
        const expenseDate = document.getElementById('expenseDate').value;
        const description = document.getElementById('description').value.trim();

        if (!category || !amount || amount <= 0 || !expenseDate) {
            showAlert(expenseAlert, 'Please fill in all required fields.', 'danger');
            return;
        }

        showLoading(btn);
        try {
            await ExpensesAPI.create(user.user_id, category, amount, expenseDate, description);
            showAlert(expenseAlert, 'Expense added successfully!', 'success');
            expenseForm.reset();
            loadExpenses(); // Refresh list
        } catch (error) {
            showAlert(expenseAlert, error.message, 'danger');
        } finally {
            hideLoading(btn);
        }
    });

    // ---- File Import ----
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const importAlert = document.getElementById('importAlert');
    const importSummary = document.getElementById('importSummary');

    uploadZone.addEventListener('click', () => fileInput.click());

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length) handleFileUpload(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleFileUpload(e.target.files[0]);
    });

    async function handleFileUpload(file) {
        // Validate file type
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['csv', 'xlsx'].includes(ext)) {
            showAlert(importAlert, 'Only .csv and .xlsx files are accepted.', 'danger');
            return;
        }

        // Validate file size (10MB)
        if (file.size > 10 * 1024 * 1024) {
            showAlert(importAlert, 'File too large. Maximum size is 10MB.', 'danger');
            return;
        }

        uploadZone.innerHTML = `
            <span class="spinner"></span>
            <p style="margin-top:0.5rem">Uploading ${file.name}...</p>
        `;

        try {
            const result = await ExpensesAPI.import(user.user_id, file);

            showAlert(importAlert, `Import complete!`, 'success');

            // Show summary
            importSummary.innerHTML = `
                <div class="import-summary">
                    <div class="import-stat inserted">
                        <div class="count text-success">${result.inserted}</div>
                        <div class="label">Inserted</div>
                    </div>
                    <div class="import-stat skipped">
                        <div class="count text-warning">${result.skipped.length}</div>
                        <div class="label">Skipped</div>
                    </div>
                </div>
                ${result.skipped.length > 0 ? `
                    <div class="card-flat" style="margin-top:1rem;">
                        <table>
                            <thead><tr><th>Row</th><th>Reason</th></tr></thead>
                            <tbody>
                                ${result.skipped.map(s => `<tr><td>${s.row}</td><td>${s.reason}</td></tr>`).join('')}
                            </tbody>
                        </table>
                    </div>
                ` : ''}
            `;
            importSummary.classList.remove('hidden');

            loadExpenses();
        } catch (error) {
            showAlert(importAlert, error.message, 'danger');
        } finally {
            // Reset upload zone
            uploadZone.innerHTML = `
                <span class="material-symbols-outlined">upload_file</span>
                <p>Drop CSV/XLSX file here or click to browse</p>
                <p class="upload-hint">Max file size: 10MB</p>
            `;
        }
    }

    // ---- Expense List ----
    const expenseTable = document.getElementById('expenseTable');
    const expenseListBody = document.getElementById('expenseListBody');
    const totalAmount = document.getElementById('totalAmount');
    const filterMonth = document.getElementById('filterMonth');
    const filterYear = document.getElementById('filterYear');

    // Populate year filter
    const currentYear = new Date().getFullYear();
    for (let y = currentYear; y >= currentYear - 5; y--) {
        filterYear.innerHTML += `<option value="${y}">${y}</option>`;
    }

    filterMonth.addEventListener('change', loadExpenses);
    filterYear.addEventListener('change', loadExpenses);

    async function loadExpenses() {
        const month = filterMonth.value || null;
        const year = filterYear.value || null;

        try {
            const result = await ExpensesAPI.list(user.user_id, month, year);

            if (result.expenses.length === 0) {
                expenseListBody.innerHTML = `
                    <tr><td colspan="5" class="text-center text-muted" style="padding:2rem;">
                        No expenses found
                    </td></tr>`;
                totalAmount.textContent = '₹0.00';
                return;
            }

            const categoryIcons = {
                food: '🍕', rent: '🏠', transport: '🚗', education: '📚',
                healthcare: '🏥', shopping: '🛒', utilities: '💡', entertainment: '🎬'
            };

            expenseListBody.innerHTML = result.expenses.map(exp => {
                const cat = exp.category.toLowerCase();
                const icon = categoryIcons[cat] || '📌';
                return `
                    <tr>
                        <td>${exp.expense_date}</td>
                        <td>
                            <span style="margin-right:0.5rem">${icon}</span>
                            ${exp.category}
                        </td>
                        <td class="font-bold">₹${exp.amount.toFixed(2)}</td>
                        <td class="text-secondary">${exp.description || '—'}</td>
                    </tr>
                `;
            }).join('');

            totalAmount.textContent = `₹${result.total.toFixed(2)}`;
            expenseTable.classList.remove('hidden');
        } catch (error) {
            showAlert(importAlert, `Failed to load expenses: ${error.message}`, 'danger');
        }
    }

    // Initial load
    loadExpenses();
});
