// Overview page: one call to /api/dashboard, then fill in the pieces.

document.addEventListener('DOMContentLoaded', async () => {
    const user = requireAuth();
    if (!user) return;
    mountHeader('dashboard');

    const $ = id => document.getElementById(id);
    const now = new Date();
    const firstName = (user.name || '').split(' ')[0];
    $('greeting').textContent = `Namaste, ${firstName}`;
    $('today').textContent = now.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    $('custNo').textContent = 'VT-' + String(user.user_id).padStart(6, '0');
    $('monthTitle').textContent = now.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });

    let data;
    try {
        data = await DashboardAPI.get(user.user_id);
    } catch (error) {
        $('monthNote').textContent = `Couldn't load your overview: ${error.message}`;
        return;
    }

    // ---- This month vs budget ----
    const spent = data.monthly_expenses;
    const budget = data.monthly_budget;
    $('custBudget').textContent = budget > 0 ? formatINR(budget, 0) : 'not set';
    $('custLoans').textContent = data.total_loans;
    if (budget > 0) {
        $('monthSpent').innerHTML = `${formatINR(spent, 0)} <span class="of">spent of ${formatINR(budget, 0)}</span>`;
        const pct = (spent / budget) * 100;
        const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
        const daysLeft = daysInMonth - now.getDate();
        if (spent > budget) {
            $('monthNote').innerHTML = `<span class="stamp">Over budget</span>&nbsp; by ${formatINR(spent - budget, 0)}, with ${daysLeft} days still to go.`;
        } else {
            const left = budget - spent;
            const perDay = daysLeft > 0 ? ` That's about ${formatINR(left / daysLeft, 0)} a day for the ${daysLeft} days left.` : '';
            $('monthNote').textContent = `${formatINR(left, 0)} left.${perDay}`;
        }
        const fill = $('monthMeterFill');
        fill.style.width = Math.min(pct, 100) + '%';
        fill.className = 'meter-fill' + (pct >= 100 ? ' red' : pct > 75 ? ' amber' : '');
        $('monthScaleMax').textContent = formatINR(budget, 0);
        $('monthMeter').hidden = false;
        $('monthScale').hidden = false;
    } else {
        $('monthSpent').textContent = formatINR(spent, 0);
        $('monthNote').innerHTML = 'spent so far. You haven\'t set a monthly budget yet. <a href="expenses.html">Set one</a> to see how you\'re doing.';
    }

    // ---- At a glance ----
    if (data.next_emi) {
        $('nextEmi').textContent = formatINR(data.next_emi.amount);
        $('nextEmiWhen').textContent = `${formatDate(data.next_emi.due_date)}, loan #${data.next_emi.loan_id}`;
    } else {
        $('nextEmi').textContent = '—';
        $('nextEmiWhen').innerHTML = 'nothing due. <a href="loans.html">Add a loan</a>';
    }

    $('owed').textContent = formatINR(data.total_outstanding_principal);
    $('loanCount').textContent = data.total_loans === 1 ? '1 loan' : `${data.total_loans} loans`;

    if (data.top_insurance) {
        $('topPlan').innerHTML = `${escapeHtml(data.top_insurance.plan_name)}<small>${Math.round(data.top_insurance.rank_score * 100)} / 100</small>`;
        $('planType').textContent = data.top_insurance.type;
    } else {
        $('topPlan').textContent = '—';
        $('planType').innerHTML = '<a href="insurance.html">Compare plans</a>';
    }

    // ---- Charts ----
    const charts = data.charts || {};
    drawBars($('trendBars'), $('trendLabels'), (charts.expense_trend || []).map((m, i, all) => ({
        label: m.label,
        value: m.total,
        current: i === all.length - 1,
        over: budget > 0 && m.total > budget
    })), budget > 0 ? budget : null);

    const split = (charts.expense_distribution || []).slice().sort((a, b) => b.total - a.total);
    $('splitYear').textContent = `${now.getFullYear()} so far`;
    if (split.length) {
        const max = split[0].total;
        const sum = split.reduce((t, c) => t + c.total, 0);
        $('categorySplit').innerHTML = split.map((c, i) => `
            <li>
                <span>${escapeHtml(c.category)}</span>
                <span class="track"><span class="fill" style="display:block; width:${(c.total / max) * 100}%; animation-delay:${i * 0.05}s"></span></span>
                <span class="amt">${formatINR(c.total, 0)}</span>
                <span class="share">${Math.round((c.total / sum) * 100)}%</span>
            </li>`).join('');
    }

    if ((charts.loan_trend || []).some(m => m.balance > 0)) {
        $('loanOutlook').hidden = false;
        drawBars($('loanBars'), $('loanLabels'), charts.loan_trend.map(m => ({
            label: m.label.split(' ')[0],
            value: m.balance
        })));
    }

    // ---- Latest entries ----
    const rows = data.recent_activity || [];
    $('recentBody').innerHTML = rows.length
        ? rows.map(e => `
            <tr>
                <td class="nowrap">${formatDate(e.date)}</td>
                <td>${escapeHtml(e.description || '—')}</td>
                <td>${escapeHtml(e.category)}${e.is_fixed ? ' <span class="tag">fixed</span>' : ''}</td>
                <td class="num">${formatINR(e.amount)}</td>
            </tr>`).join('')
        : '<tr><td colspan="4" class="empty">No expenses yet. <a href="expenses.html">Add your first one.</a></td></tr>';
});

// Simple column chart out of divs. Heights are relative to the tallest bar
// (or the budget, if that's higher), and an optional dashed line marks the budget.
function drawBars(barsEl, labelsEl, items, budgetLine = null) {
    if (!items.length) {
        barsEl.innerHTML = '<p class="muted small" style="align-self:center; margin:auto;">No data yet.</p>';
        return;
    }
    const max = Math.max(...items.map(i => i.value), budgetLine || 0, 1);
    const line = budgetLine
        ? `<div class="budget-line" style="bottom:${(budgetLine / max) * 85}%"><span>budget ${shortINR(budgetLine)}</span></div>`
        : '';
    barsEl.innerHTML = line + items.map(i => `
        <div class="bar${i.current ? ' current' : ''}" title="${escapeHtml(i.label)}: ${formatINR(i.value, 0)}">
            <span class="bar-value">${i.value ? shortINR(i.value) : ''}</span>
            <span class="bar-col${i.over ? ' over' : ''}" style="height:${(i.value / max) * 85}%"></span>
        </div>`).join('');
    labelsEl.innerHTML = items.map(i => `<span>${escapeHtml(i.label)}</span>`).join('');
}

// 17471 -> "17.5k", 488855 -> "4.9L"
function shortINR(n) {
    if (n >= 100000) return (n / 100000).toFixed(1).replace(/\.0$/, '') + 'L';
    if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
    return Math.round(n).toString();
}
