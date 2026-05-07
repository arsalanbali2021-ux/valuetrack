// Expenses page: add an expense, keep the monthly budget, list the ledger.

document.addEventListener('DOMContentLoaded', () => {
    const user = requireAuth();
    if (!user) return;
    mountHeader('expenses');

    const $ = id => document.getElementById(id);
    const now = new Date();
    const thisMonth = now.getMonth() + 1;
    const thisYear = now.getFullYear();
    const expenseAlert = $('expenseAlert');

    $('expenseDate').value = now.toISOString().slice(0, 10);

    // ---- Add ----
    $('expenseForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const form = e.target;
        const btn = form.querySelector('button[type="submit"]');
        const category = $('category').value;
        const amount = parseFloat($('amount').value);
        const date = $('expenseDate').value;

        if (!category || !(amount > 0) || !date) {
            return showAlert(expenseAlert, 'Amount, date and category are needed.');
        }

        showLoading(btn);
        try {
            await ExpensesAPI.create(user.user_id, category, amount, date, $('description').value.trim(), $('isFixed').checked);
            showAlert(expenseAlert, `Saved ${formatINR(amount)} under ${escapeHtml(category)}.`, 'success');
            form.reset();
            $('expenseDate').value = date;
            await Promise.all([loadLedger(), loadMonthTotal()]);
        } catch (error) {
            showAlert(expenseAlert, escapeHtml(error.message));
        } finally {
            hideLoading(btn);
        }
    });

    // ---- Budget (always compared with the current month) ----
    let budget = parseFloat(user.monthly_budget) || 0;
    let monthSpent = 0;

    function drawBudget() {
        const monthName = now.toLocaleDateString('en-IN', { month: 'long' });
        if (budget > 0) {
            $('budgetSpent').innerHTML = `${formatINR(monthSpent, 0)} <span class="of">of ${formatINR(budget, 0)}</span>`;
            const pct = (monthSpent / budget) * 100;
            $('budgetNote').innerHTML = monthSpent > budget
                ? `<span class="stamp">Over budget</span>&nbsp; ${monthName} is ${formatINR(monthSpent - budget, 0)} over.`
                : `spent in ${monthName}. ${formatINR(budget - monthSpent, 0)} left.`;
            $('budgetBar').style.width = Math.min(pct, 100) + '%';
            $('budgetBar').className = 'meter-fill' + (pct >= 100 ? ' red' : pct > 75 ? ' amber' : '');
            $('budgetMax').textContent = formatINR(budget, 0);
        } else {
            $('budgetSpent').textContent = formatINR(monthSpent, 0);
            $('budgetNote').textContent = `spent in ${monthName}. No budget set yet.`;
            $('budgetBar').style.width = '0';
            $('budgetMax').textContent = '—';
        }
    }

    async function loadMonthTotal() {
        try {
            const result = await ExpensesAPI.list(user.user_id, thisMonth, thisYear);
            monthSpent = result.total;
        } catch (error) {
            monthSpent = 0;
        }
        drawBudget();
    }

    $('editBudgetBtn').addEventListener('click', () => {
        $('budgetDisplay').classList.add('hidden');
        $('budgetEditor').classList.remove('hidden');
        $('budgetInput').value = budget || '';
        $('budgetInput').focus();
    });

    $('budgetEditor').addEventListener('submit', async (e) => {
        e.preventDefault();
        const value = parseFloat($('budgetInput').value);
        if (isNaN(value) || value < 0) return;
        const btn = $('saveBudgetBtn');
        showLoading(btn);
        try {
            await AuthAPI.setBudget(user.user_id, value);
            budget = value;
            user.monthly_budget = value;
            localStorage.setItem('valuetrack_user', JSON.stringify(user));
            $('budgetEditor').classList.add('hidden');
            $('budgetDisplay').classList.remove('hidden');
            drawBudget();
        } catch (error) {
            showAlert(expenseAlert, `Couldn't save the budget: ${escapeHtml(error.message)}`);
        } finally {
            hideLoading(btn);
        }
    });

    // ---- Ledger ----
    const filterMonth = $('filterMonth');
    const filterYear = $('filterYear');
    for (let y = thisYear; y >= thisYear - 5; y--) {
        filterYear.insertAdjacentHTML('beforeend', `<option value="${y}">${y}</option>`);
    }
    filterMonth.value = String(thisMonth);
    filterYear.value = String(thisYear);
    filterMonth.addEventListener('change', loadLedger);
    filterYear.addEventListener('change', loadLedger);

    async function loadLedger() {
        const month = filterMonth.value || null;
        const year = filterYear.value || null;
        const body = $('expenseListBody');
        try {
            const result = await ExpensesAPI.list(user.user_id, month, year);
            body.innerHTML = result.expenses.length
                ? result.expenses.map(e => `
                    <tr>
                        <td class="nowrap">${formatDate(e.expense_date)}</td>
                        <td>${escapeHtml(e.description || '—')}</td>
                        <td>${escapeHtml(e.category)}${e.is_fixed ? ' <span class="tag">fixed</span>' : ''}</td>
                        <td class="num">${formatINR(e.amount)}</td>
                    </tr>`).join('')
                : '<tr><td colspan="4" class="empty">Nothing recorded for this period.</td></tr>';

            const fixed = result.expenses.filter(e => e.is_fixed).reduce((s, e) => s + e.amount, 0);
            $('totalLabel').textContent = `Total, ${result.count} ${result.count === 1 ? 'entry' : 'entries'}` +
                (fixed ? ` (fixed: ${formatINR(fixed, 0)})` : '');
            $('totalAmount').textContent = formatINR(result.total);
        } catch (error) {
            body.innerHTML = `<tr><td colspan="4" class="empty">Couldn't load expenses: ${escapeHtml(error.message)}</td></tr>`;
        }
    }

    loadLedger();
    loadMonthTotal();
});
