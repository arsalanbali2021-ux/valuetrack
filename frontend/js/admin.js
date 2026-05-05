/**
 * ValueTrack — Admin Panel Logic
 * Insurance CRUD, IRDAI catalogue import, Expense Categories, Users list.
 */

document.addEventListener('DOMContentLoaded', () => {
    const user = requireAuth();
    if (!user) return;

    // Block non-admin users
    if (user.role !== 'admin') {
        window.location.href = 'dashboard.html';
        return;
    }

    const userNameEl = document.getElementById('userName');
    if (userNameEl) userNameEl.textContent = user.name;

    // ---- Tab navigation ----
    const tabBtns = document.querySelectorAll('.admin-tab-btn');
    const tabPanels = document.querySelectorAll('.admin-tab-panel');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanels.forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`tab-${target}`).classList.add('active');
        });
    });

    // ====================================================================
    // INSURANCE MANAGEMENT
    // ====================================================================
    const insuranceTableBody = document.getElementById('insuranceTableBody');
    const insuranceAlert = document.getElementById('insuranceAlert');
    const planModal = document.getElementById('planModal');
    const planForm = document.getElementById('planForm');
    const planModalTitle = document.getElementById('planModalTitle');

    let plansCache = [];

    function yesNo(val) {
        return val ? '<span class="badge badge-success">Yes</span>' : '<span class="badge badge-muted">No</span>';
    }

    async function loadInsuranceWithCache() {
        try {
            plansCache = await AdminAPI.getInsurance(user.user_id);
            renderInsuranceTable(plansCache);
        } catch (error) {
            showAlert(insuranceAlert, error.message, 'danger');
        }
    }

    function renderInsuranceTable(plans) {
        if (!plans.length) {
            insuranceTableBody.innerHTML = '<tr><td colspan="11" class="text-center text-muted" style="padding:2rem;">No insurance plans found.</td></tr>';
            return;
        }
        insuranceTableBody.innerHTML = plans.map(p => `
            <tr>
                <td>${p.insurance_id}</td>
                <td><strong>${escapeHtml(p.plan_name)}</strong>${p.irdai_uin ? `<br><span class="badge badge-info" title="IRDAI UIN" style="margin-top:4px;">${escapeHtml(p.irdai_uin)}</span>` : ''}</td>
                <td>${p.plan_type}</td>
                <td>${p.min_age}–${p.max_age}</td>
                <td style="text-align:right;">₹${Number(p.monthly_premium).toLocaleString()}</td>
                <td style="text-align:right;">₹${Number(p.coverage_amount).toLocaleString()}</td>
                <td>${yesNo(p.has_critical_illness)}</td>
                <td>${yesNo(p.has_maternity)}</td>
                <td>${yesNo(p.has_accident)}</td>
                <td>${p.co_pay_percentage}%</td>
                <td>
                    <div class="flex gap-1">
                        <button class="icon-btn" title="Edit" onclick="editPlan(${p.insurance_id})">
                            <span class="material-symbols-outlined" style="font-size:1rem;">edit</span>
                        </button>
                        <button class="icon-btn" title="Delete" onclick="deletePlan(${p.insurance_id}, '${p.plan_name.replace(/'/g, "\\'")}')">
                            <span class="material-symbols-outlined" style="font-size:1rem; color:var(--color-danger);">delete</span>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    // Open plan modal (add)
    document.getElementById('btnAddPlan').addEventListener('click', () => {
        planModalTitle.textContent = 'Add Insurance Plan';
        planForm.reset();
        document.getElementById('planId').value = '';
        openModal(planModal);
    });

    // Close modal handlers
    document.getElementById('closePlanModal').addEventListener('click', () => closeModal(planModal));
    document.getElementById('cancelPlanModal').addEventListener('click', () => closeModal(planModal));

    // Edit plan
    window.editPlan = function(planId) {
        const plan = plansCache.find(p => p.insurance_id === planId);
        if (!plan) return;

        planModalTitle.textContent = 'Edit Insurance Plan';
        document.getElementById('planId').value = plan.insurance_id;
        document.getElementById('planName').value = plan.plan_name;
        document.getElementById('planType').value = plan.plan_type;
        document.getElementById('planMinAge').value = plan.min_age;
        document.getElementById('planMaxAge').value = plan.max_age;
        document.getElementById('planPremium').value = plan.monthly_premium;
        document.getElementById('planCoverage').value = plan.coverage_amount;
        document.getElementById('planCoPay').value = plan.co_pay_percentage || 0;
        document.getElementById('planCritical').checked = plan.has_critical_illness;
        document.getElementById('planMaternity').checked = plan.has_maternity;
        document.getElementById('planAccident').checked = plan.has_accident;
        document.getElementById('planUin').value = plan.irdai_uin || '';
        openModal(planModal);
    };

    // Start a new plan pre-filled from an IRDAI product
    window.createPlanFromIrdai = function(uin) {
        const product = irdaiCache.find(p => p.uin === uin);
        if (!product) return;

        planModalTitle.textContent = 'Create Plan from IRDAI Product';
        planForm.reset();
        document.getElementById('planId').value = '';
        document.getElementById('planName').value = product.product_name;
        document.getElementById('planUin').value = product.uin;
        const typeSelect = document.getElementById('planType');
        if ([...typeSelect.options].some(o => o.value === product.product_type)) {
            typeSelect.value = product.product_type;
        }
        openModal(planModal);
    };

    // Save plan (create or update)
    planForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('savePlanBtn');
        const planId = document.getElementById('planId').value;

        const data = {
            user_id: user.user_id,
            plan_name: document.getElementById('planName').value,
            plan_type: document.getElementById('planType').value,
            min_age: parseInt(document.getElementById('planMinAge').value),
            max_age: parseInt(document.getElementById('planMaxAge').value),
            monthly_premium: parseFloat(document.getElementById('planPremium').value),
            coverage_amount: parseFloat(document.getElementById('planCoverage').value),
            co_pay_percentage: parseInt(document.getElementById('planCoPay').value) || 0,
            has_critical_illness: document.getElementById('planCritical').checked,
            has_maternity: document.getElementById('planMaternity').checked,
            has_accident: document.getElementById('planAccident').checked,
            irdai_uin: document.getElementById('planUin').value.trim()
        };

        showLoading(btn);
        try {
            if (planId) {
                await AdminAPI.updateInsurance(planId, data, user.user_id);
                showAlert(insuranceAlert, 'Plan updated successfully!', 'success');
            } else {
                await AdminAPI.createInsurance(data, user.user_id);
                showAlert(insuranceAlert, 'Plan created successfully!', 'success');
            }
            closeModal(planModal);
            await loadInsuranceWithCache();
            if (data.irdai_uin) await loadIrdai();
        } catch (error) {
            showAlert(insuranceAlert, error.message, 'danger');
        } finally {
            hideLoading(btn);
        }
    });

    // Delete plan
    window.deletePlan = function(planId, planName) {
        showDeleteConfirm(`Are you sure you want to delete "${planName}"? This will also remove it from future recommendations.`, async () => {
            try {
                await AdminAPI.deleteInsurance(planId, user.user_id);
                showAlert(insuranceAlert, 'Plan deleted successfully!', 'success');
                await loadInsuranceWithCache();
            } catch (error) {
                showAlert(insuranceAlert, error.message, 'danger');
            }
        });
    };

    // ====================================================================
    // IRDAI CATALOGUE
    // ====================================================================
    const irdaiAlert = document.getElementById('irdaiAlert');
    const irdaiTableBody = document.getElementById('irdaiTableBody');
    const irdaiSearch = document.getElementById('irdaiSearch');
    const irdaiType = document.getElementById('irdaiType');
    const irdaiCount = document.getElementById('irdaiCount');
    const irdaiPrev = document.getElementById('irdaiPrev');
    const irdaiNext = document.getElementById('irdaiNext');
    const IRDAI_PAGE = 25;
    let irdaiCache = [];
    let irdaiOffset = 0;
    let irdaiTotal = 0;

    async function loadIrdai() {
        try {
            const data = await AdminAPI.getIrdaiProducts(user.user_id, {
                q: irdaiSearch.value.trim(),
                type: irdaiType.value,
                limit: IRDAI_PAGE,
                offset: irdaiOffset
            });
            irdaiCache = data.items;
            irdaiTotal = data.total;

            // Keep the type filter in sync with what's been imported
            const current = irdaiType.value;
            irdaiType.innerHTML = '<option value="">All types</option>' +
                data.types.map(t => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');
            irdaiType.value = current;

            renderIrdai();
        } catch (error) {
            irdaiTableBody.innerHTML = `<tr><td colspan="7" class="text-center text-danger" style="padding:2rem;">${escapeHtml(error.message)}</td></tr>`;
        }
    }

    function renderIrdai() {
        const from = irdaiTotal ? irdaiOffset + 1 : 0;
        const to = irdaiOffset + irdaiCache.length;
        irdaiCount.textContent = `${from}–${to} of ${irdaiTotal} products`;
        irdaiPrev.disabled = irdaiOffset === 0;
        irdaiNext.disabled = to >= irdaiTotal;

        if (!irdaiCache.length) {
            irdaiTableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding:2rem;">${
                irdaiSearch.value || irdaiType.value
                    ? 'No products match your search.'
                    : 'No IRDAI products yet. Import the list above to get started.'
            }</td></tr>`;
            return;
        }

        irdaiTableBody.innerHTML = irdaiCache.map(p => `
            <tr>
                <td><code style="font-size:0.8rem;">${escapeHtml(p.uin)}</code></td>
                <td><strong>${escapeHtml(p.product_name)}</strong></td>
                <td class="text-sm">${escapeHtml(p.insurer_name)}</td>
                <td>${escapeHtml(p.product_type || '—')}</td>
                <td class="text-muted" style="white-space:nowrap;">${p.approval_date ? p.approval_date.split('-').reverse().join('-') : '—'}</td>
                <td>${p.is_archived
                    ? '<span class="badge badge-neutral">Archived</span>'
                    : '<span class="badge badge-success">Active</span>'}</td>
                <td>${p.linked_plan_ids.length
                    ? p.linked_plan_ids.map(id => `<span class="badge badge-primary">Plan #${id}</span>`).join(' ')
                    : `<button class="btn btn-outline btn-sm" onclick="createPlanFromIrdai('${escapeHtml(p.uin)}')">
                           <span class="material-symbols-outlined" style="font-size:1rem;">add</span> Create plan
                       </button>`}</td>
            </tr>
        `).join('');
    }

    document.getElementById('irdaiImportForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('irdaiImportBtn');
        const fileInput = document.getElementById('irdaiFile');
        const textInput = document.getElementById('irdaiText');
        const file = fileInput.files[0];
        const text = textInput.value.trim();

        if (!file && !text) {
            showAlert(irdaiAlert, 'Choose a saved IRDAI page / CSV, or paste the copied table.', 'danger');
            return;
        }

        showLoading(btn);
        try {
            const summary = await AdminAPI.importIrdai(file || text, user.user_id);
            let msg = `Found ${summary.rows_found} row${summary.rows_found === 1 ? '' : 's'}: ${summary.added} new, ${summary.updated} updated` +
                      (summary.skipped ? `, ${summary.skipped} skipped` : '') +
                      `. Catalogue now has ${summary.total_in_catalogue} products.`;
            if (summary.errors.length) {
                msg += '<br><span class="text-xs">' + summary.errors.map(escapeHtml).join('<br>') + '</span>';
            }
            showAlert(irdaiAlert, msg, summary.skipped ? 'info' : 'success');
            fileInput.value = '';
            textInput.value = '';
            irdaiOffset = 0;
            await loadIrdai();
        } catch (error) {
            showAlert(irdaiAlert, escapeHtml(error.message), 'danger');
        } finally {
            hideLoading(btn);
        }
    });

    let searchTimer = null;
    irdaiSearch.addEventListener('input', () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => { irdaiOffset = 0; loadIrdai(); }, 300);
    });
    irdaiType.addEventListener('change', () => { irdaiOffset = 0; loadIrdai(); });
    irdaiPrev.addEventListener('click', () => { irdaiOffset = Math.max(0, irdaiOffset - IRDAI_PAGE); loadIrdai(); });
    irdaiNext.addEventListener('click', () => { irdaiOffset += IRDAI_PAGE; loadIrdai(); });

    // ====================================================================
    // EXPENSE CATEGORIES
    // ====================================================================
    const categoriesTableBody = document.getElementById('categoriesTableBody');
    const categoriesAlert = document.getElementById('categoriesAlert');
    const categoryModal = document.getElementById('categoryModal');
    const categoryForm = document.getElementById('categoryForm');
    const categoryModalTitle = document.getElementById('categoryModalTitle');
    let categoriesCache = [];

    async function loadCategories() {
        try {
            categoriesCache = await AdminAPI.getCategories(user.user_id);
            if (!categoriesCache.length) {
                categoriesTableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted" style="padding:2rem;">No categories found.</td></tr>';
                return;
            }
            categoriesTableBody.innerHTML = categoriesCache.map(c => `
                <tr>
                    <td>${c.category_id}</td>
                    <td><span class="material-symbols-outlined" style="font-size:1.25rem; color:var(--color-primary);">${c.icon || 'category'}</span></td>
                    <td><strong>${c.category_name}</strong></td>
                    <td>
                        <div class="flex gap-1">
                            <button class="icon-btn" title="Edit" onclick="editCategory(${c.category_id})">
                                <span class="material-symbols-outlined" style="font-size:1rem;">edit</span>
                            </button>
                            <button class="icon-btn" title="Delete" onclick="deleteCategory(${c.category_id}, '${c.category_name.replace(/'/g, "\\'")}')">
                                <span class="material-symbols-outlined" style="font-size:1rem; color:var(--color-danger);">delete</span>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
        } catch (error) {
            showAlert(categoriesAlert, error.message, 'danger');
        }
    }

    document.getElementById('btnAddCategory').addEventListener('click', () => {
        categoryModalTitle.textContent = 'Add Category';
        categoryForm.reset();
        document.getElementById('categoryId').value = '';
        openModal(categoryModal);
    });

    document.getElementById('closeCategoryModal').addEventListener('click', () => closeModal(categoryModal));
    document.getElementById('cancelCategoryModal').addEventListener('click', () => closeModal(categoryModal));

    window.editCategory = function(catId) {
        const cat = categoriesCache.find(c => c.category_id === catId);
        if (!cat) return;

        categoryModalTitle.textContent = 'Edit Category';
        document.getElementById('categoryId').value = cat.category_id;
        document.getElementById('categoryName').value = cat.category_name;
        document.getElementById('categoryIcon').value = cat.icon || '';
        openModal(categoryModal);
    };

    categoryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('saveCategoryBtn');
        const catId = document.getElementById('categoryId').value;

        const data = {
            user_id: user.user_id,
            category_name: document.getElementById('categoryName').value,
            icon: document.getElementById('categoryIcon').value || 'category'
        };

        showLoading(btn);
        try {
            if (catId) {
                await AdminAPI.updateCategory(catId, data, user.user_id);
                showAlert(categoriesAlert, 'Category updated!', 'success');
            } else {
                await AdminAPI.createCategory(data, user.user_id);
                showAlert(categoriesAlert, 'Category created!', 'success');
            }
            closeModal(categoryModal);
            await loadCategories();
        } catch (error) {
            showAlert(categoriesAlert, error.message, 'danger');
        } finally {
            hideLoading(btn);
        }
    });

    window.deleteCategory = function(catId, catName) {
        showDeleteConfirm(`Are you sure you want to delete the "${catName}" category?`, async () => {
            try {
                await AdminAPI.deleteCategory(catId, user.user_id);
                showAlert(categoriesAlert, 'Category deleted!', 'success');
                await loadCategories();
            } catch (error) {
                showAlert(categoriesAlert, error.message, 'danger');
            }
        });
    };

    // ====================================================================
    // USERS (read-only)
    // ====================================================================
    const usersTableBody = document.getElementById('usersTableBody');

    async function loadUsers() {
        try {
            const users = await AdminAPI.getUsers(user.user_id);
            if (!users.length) {
                usersTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding:2rem;">No users found.</td></tr>';
                return;
            }
            usersTableBody.innerHTML = users.map(u => `
                <tr>
                    <td>${u.user_id}</td>
                    <td><strong>${u.name}</strong></td>
                    <td>${u.email}</td>
                    <td>${u.role === 'admin' ? '<span class="badge badge-warning">Admin</span>' : '<span class="badge badge-muted">User</span>'}</td>
                    <td class="text-muted">${u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
                </tr>
            `).join('');
        } catch (error) {
            usersTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-danger" style="padding:2rem;">${error.message}</td></tr>`;
        }
    }

    // ====================================================================
    // MODAL UTILITIES
    // ====================================================================
    function openModal(modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    function closeModal(modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }

    // Delete confirmation
    const deleteModal = document.getElementById('deleteModal');
    let pendingDeleteFn = null;

    window.showDeleteConfirm = function(message, onConfirm) {
        document.getElementById('deleteMessage').textContent = message;
        pendingDeleteFn = onConfirm;
        openModal(deleteModal);
    };

    document.getElementById('closeDeleteModal').addEventListener('click', () => closeModal(deleteModal));
    document.getElementById('cancelDeleteModal').addEventListener('click', () => closeModal(deleteModal));
    document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
        closeModal(deleteModal);
        if (pendingDeleteFn) {
            await pendingDeleteFn();
            pendingDeleteFn = null;
        }
    });

    // Close modals on overlay click
    [planModal, categoryModal, deleteModal].forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal(modal);
        });
    });

    // ====================================================================
    // INITIAL LOAD
    // ====================================================================
    loadInsuranceWithCache();
    loadIrdai();
    loadCategories();
    loadUsers();
});
