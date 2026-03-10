/**
 * ValueTrack — Expenses Page Logic
 * Manual add and expense listing.
 */

document.addEventListener('DOMContentLoaded', () => {
    const user = requireAuth();
    if (!user) return;

    const userNameEl = document.getElementById('userName');
    if (userNameEl) userNameEl.textContent = user.name;

    // Show admin link if admin
    if (user.role === 'admin') {
        const adminLink = document.getElementById('adminLink');
        if (adminLink) adminLink.style.display = '';
    }

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
        const isFixed = document.getElementById('isFixed').checked;

        if (!category || !amount || amount <= 0 || !expenseDate) {
            showAlert(expenseAlert, 'Please fill in all required fields.', 'danger');
            return;
        }

        showLoading(btn);
        try {
            await ExpensesAPI.create(user.user_id, category, amount, expenseDate, description, isFixed);
            showAlert(expenseAlert, 'Expense added successfully!', 'success');
            expenseForm.reset();
            loadExpenses();
        } catch (error) {
            showAlert(expenseAlert, error.message, 'danger');
        } finally {
            hideLoading(btn);
        }
    });

    // ---- Budget Logic ----
    let currentBudget = parseFloat(user.monthly_budget) || 0.0;
    const editBudgetBtn = document.getElementById('editBudgetBtn');
    const saveBudgetBtn = document.getElementById('saveBudgetBtn');
    const budgetDisplay = document.getElementById('budgetDisplay');
    const budgetEditor = document.getElementById('budgetEditor');
    const budgetInput = document.getElementById('budgetInput');
    const budgetStatus = document.getElementById('budgetStatus');
    const budgetBar = document.getElementById('budgetBar');

    if (editBudgetBtn) {
        editBudgetBtn.addEventListener('click', (e) => {
            e.preventDefault();
            budgetDisplay.style.display = 'none';
            budgetEditor.style.display = 'flex';
            budgetInput.value = currentBudget || '';
        });
    }

    if (saveBudgetBtn) {
        saveBudgetBtn.addEventListener('click', async () => {
            const newBudget = parseFloat(budgetInput.value);
            if (isNaN(newBudget) || newBudget < 0) return;

            const originalText = saveBudgetBtn.textContent;
            saveBudgetBtn.textContent = '...';
            try {
                await AuthAPI.setBudget(user.user_id, newBudget);
                currentBudget = newBudget;
                // update local storage
                user.monthly_budget = currentBudget;
                localStorage.setItem('valuetrack_user', JSON.stringify(user));
                
                budgetEditor.style.display = 'none';
                budgetDisplay.style.display = 'block';
                updateBudgetUI(parseFloat(totalAmount.textContent.replace('₹', '')) || 0);
            } catch (error) {
                alert('Failed to save budget: ' + error.message);
            } finally {
                saveBudgetBtn.textContent = originalText;
            }
        });
    }

    function updateBudgetUI(totalSpent) {
        if (!budgetStatus) return;
        budgetStatus.textContent = `₹${totalSpent.toLocaleString()} / ₹${currentBudget.toLocaleString()}`;
        
        let pct = 0;
        if (currentBudget > 0) {
            pct = (totalSpent / currentBudget) * 100;
        }
        
        if (pct > 100) pct = 100;
        budgetBar.style.width = `${pct}%`;
        
        if (pct < 60) {
            budgetBar.style.backgroundColor = 'var(--color-success, #10b981)';
        } else if (pct < 90) {
            budgetBar.style.backgroundColor = 'var(--color-warning, #f59e0b)';
        } else {
            budgetBar.style.backgroundColor = 'var(--color-danger, #ef4444)';
        }
    }

    // ---- Expense List ----
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
                    <tr><td colspan="4" class="text-center text-muted" style="padding:2rem;">
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
                const fixedBadge = exp.is_fixed ? `<span class="badge" style="font-size:0.65rem; padding:0.1rem 0.4rem; background:var(--color-surface-hover); color:var(--color-text-secondary); margin-left:0.5rem; border-radius:4px; font-weight:700;">FIXED</span>` : '';
                return `
                    <tr>
                        <td>${exp.expense_date}</td>
                        <td>
                            <span style="display:inline-flex; align-items:center;">
                                <span style="margin-right:4px;">${icon}</span>
                                ${exp.category}
                                ${fixedBadge}
                            </span>
                        </td>
                        <td class="font-bold">₹${exp.amount.toFixed(2)}</td>
                        <td class="text-secondary">${exp.description || '—'}</td>
                    </tr>
                `;
            }).join('');

            totalAmount.textContent = `₹${result.total.toFixed(2)}`;
            updateBudgetUI(result.total);
        } catch (error) {
            showAlert(expenseAlert, `Failed to load expenses: ${error.message}`, 'danger');
        }
    }

    // Initial load
    loadExpenses();
});
