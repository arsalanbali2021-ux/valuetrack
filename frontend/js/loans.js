// Loans page: create a loan, or open one by its number, and show the schedule.

document.addEventListener('DOMContentLoaded', () => {
    const user = requireAuth();
    if (!user) return;
    mountHeader('loans');

    const $ = id => document.getElementById(id);
    const loanForm = $('loanForm');
    const loanAlert = $('loanAlert');

    $('startDate').value = new Date().toISOString().slice(0, 10);

    loanForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = loanForm.querySelector('button[type="submit"]');
        const principal = parseFloat($('principal').value);
        const rate = parseFloat($('interestRate').value);
        const tenure = parseInt($('tenure').value, 10);
        const startDate = $('startDate').value;

        if (!(principal > 0)) return showAlert(loanAlert, 'The loan amount has to be more than zero.');
        if (!(rate >= 0)) return showAlert(loanAlert, "The interest rate can't be negative.");
        if (!(tenure > 0)) return showAlert(loanAlert, 'Tenure has to be at least 1 month.');
        if (!startDate) return showAlert(loanAlert, 'Pick the date the loan was taken.');

        showLoading(btn);
        try {
            const result = await LoansAPI.create(user.user_id, principal, rate, tenure, startDate);
            showAlert(loanAlert, `Saved as loan #${result.loan_id}. EMI is ${formatINR(result.emi)} a month.`, 'success');
            $('lookupId').value = result.loan_id;
            await showSchedule(result.loan_id);
        } catch (error) {
            showAlert(loanAlert, escapeHtml(error.message));
        } finally {
            hideLoading(btn);
        }
    });

    $('lookupForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = parseInt($('lookupId').value, 10);
        if (id > 0) {
            try {
                await showSchedule(id);
            } catch (error) {
                showAlert(loanAlert, `Couldn't open loan #${id}: ${escapeHtml(error.message)}`);
            }
        }
    });

    async function showSchedule(loanId) {
        const { loan, schedule } = await LoansAPI.getSchedule(loanId);

        const totalPaid = schedule.reduce((sum, r) => sum + r.emi_amount, 0);
        const totalInterest = schedule.reduce((sum, r) => sum + r.interest_component, 0);
        const today = new Date().toISOString().slice(0, 10);
        const next = schedule.find(r => r.due_date >= today);

        $('scheduleTitle').textContent = `Loan #${loan.loan_id}: ${formatINR(loan.principal, 0)} at ${loan.annual_interest_rate}% for ${loan.tenure_months} months`;
        $('scheduleMeta').textContent = `taken on ${formatDate(loan.start_date)}`;
        $('loanSummary').innerHTML = `
            <div><dt>Monthly EMI</dt><dd>${formatINR(schedule[0].emi_amount)}</dd></div>
            <div><dt>Total interest</dt><dd>${formatINR(totalInterest)}</dd></div>
            <div><dt>Total you pay back</dt><dd>${formatINR(totalPaid)}</dd></div>
            <div><dt>Next EMI</dt><dd>${next ? formatDate(next.due_date) : 'all paid'}</dd></div>`;

        // One group row per calendar year, like a passbook page break
        let lastYear = null;
        $('scheduleBody').innerHTML = schedule.map(r => {
            const year = r.due_date.slice(0, 4);
            const group = year !== lastYear ? `<tr class="group"><td colspan="6">${year}</td></tr>` : '';
            lastYear = year;
            const isNext = next && r.month_no === next.month_no;
            const isPaid = r.due_date < today;
            const cls = isNext ? ' id="nextRow" class="is-next"' : isPaid ? ' class="is-paid"' : '';
            return `${group}
                <tr${cls}>
                    <td class="num">${r.month_no}</td>
                    <td class="nowrap">${formatDate(r.due_date)}${isNext ? ' <span class="tag amber">due next</span>' : isPaid ? '<span class="paid">PAID</span>' : ''}</td>
                    <td class="num">${formatINR(r.emi_amount)}</td>
                    <td class="num">${formatINR(r.interest_component)}</td>
                    <td class="num">${formatINR(r.principal_component)}</td>
                    <td class="num">${formatINR(r.remaining_balance)}</td>
                </tr>`;
        }).join('');

        $('scheduleSection').classList.remove('hidden');
        $('scheduleSection').scrollIntoView({ block: 'start' });

        // Inside the table, jump to the next unpaid EMI (keep a couple of paid rows above it)
        const wrap = $('scheduleSection').querySelector('.table-wrap');
        const nextRow = $('nextRow');
        wrap.scrollTop = nextRow ? Math.max(0, nextRow.offsetTop - wrap.querySelector('thead').offsetHeight - 80) : 0;
    }
});
