// Insurance page: send the profile, show the ranked plans with their reasons.

// The backend tags each reason with an icon name; turn that into ✓ / ✗ / ! / +
const REASON_KIND = {
    check_circle: 'yes', payments: 'yes', health_and_safety: 'yes', pregnant_woman: 'yes',
    personal_injury: 'yes', verified: 'yes', error: 'no', warning: 'warn', info: 'extra'
};

document.addEventListener('DOMContentLoaded', () => {
    const user = requireAuth();
    if (!user) return;
    mountHeader('insurance');

    const $ = id => document.getElementById(id);
    const form = $('insuranceForm');
    const alertBox = $('insuranceAlert');
    const list = $('resultsList');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = form.querySelector('button[type="submit"]');
        const age = parseInt($('age').value, 10);
        const budget = parseFloat($('budget').value);
        const source = $('planSource').value;

        if (!(age >= 1 && age <= 120)) return showAlert(alertBox, 'Age has to be between 1 and 120.');
        if (!(budget >= 0)) return showAlert(alertBox, "Budget can't be negative.");
        alertBox.innerHTML = '';

        showLoading(btn);
        try {
            const result = await InsuranceAPI.getRecommendation(
                user.user_id, age, budget,
                $('needsCriticalIllness').checked, $('needsMaternity').checked, $('needsAccident').checked,
                source
            );

            $('resultsCaption').textContent = source === 'irdai' ? 'IRDAI-registered plans only' : 'all plans';

            if (!result.top || !result.top.length) {
                $('resultsTitle').textContent = 'No plans fit';
                list.innerHTML = `<p>${escapeHtml(explainEmpty(result.reason))}</p>
                    <p class="muted small">Try a higher monthly budget, or untick one of the covers.</p>`;
                return;
            }

            $('resultsTitle').textContent = result.top.length === 1 ? 'Best fit' : `Top ${result.top.length} fits`;
            list.innerHTML = result.top.map(renderPlan).join('');
        } catch (error) {
            showAlert(alertBox, escapeHtml(error.message));
        } finally {
            hideLoading(btn);
        }
    });
});

function explainEmpty(reason) {
    if (!reason) return 'No plan matched your age and budget.';
    if (reason === 'no eligible plans fit your criteria') return 'No plan matched your age and budget.';
    if (reason === 'no policies in database') return 'There are no plans in the database yet.';
    return reason;
}

function renderPlan(plan) {
    const irdai = plan.irdai;
    const reasons = (plan.explanations || []).map(r =>
        `<li class="${REASON_KIND[r.icon] || 'extra'}">${escapeHtml(r.text)}</li>`).join('');

    return `
        <article class="plan">
            <div class="plan-rank">${plan.rank}</div>
            <div>
                <h3>${escapeHtml(plan.plan_name)}${plan.rank === 1 ? '<span class="first-pick">best fit</span>' : ''}</h3>
                <p class="sub">${escapeHtml(plan.type)}${irdai ? `, ${escapeHtml(irdai.insurer)}` : ''}</p>
            </div>
            <div class="plan-score">
                <div class="seal" title="Match score out of 100"><span class="fig">${Math.round(plan.score * 100)}</span><small>of 100</small></div>
            </div>
            <div class="plan-terms">
                <span>Premium <b>${formatINR(plan.premium, 0)}</b>/month</span>
                <span>Cover <b>${formatINR(plan.coverage, 0)}</b></span>
                <span>Ages <b>${plan.min_age}–${plan.max_age}</b></span>
                <span>Co-pay <b>${plan.co_pay}%</b></span>
                ${irdai ? `<span>UIN <b>${escapeHtml(irdai.uin)}</b>${irdai.approval_date ? `, approved ${formatDate(irdai.approval_date)}` : ''}</span>` : ''}
            </div>
            <ul class="reasons">${reasons}</ul>
        </article>`;
}
