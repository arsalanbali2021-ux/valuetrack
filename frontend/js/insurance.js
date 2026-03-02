/**
 * ValueTrack — Insurance Page Logic
 * Eligibility form + ranked top-5 results display.
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

    const insuranceForm = document.getElementById('insuranceForm');
    const insuranceAlert = document.getElementById('insuranceAlert');
    const resultsSection = document.getElementById('resultsSection');
    const resultsList = document.getElementById('resultsList');

    insuranceForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = insuranceForm.querySelector('button[type="submit"]');

        const age = parseInt(document.getElementById('age').value);
        const budget = parseFloat(document.getElementById('budget').value);
        const needsCriticalIllness = document.getElementById('needsCriticalIllness').checked;
        const needsMaternity = document.getElementById('needsMaternity').checked;
        const needsAccident = document.getElementById('needsAccident').checked;

        // Validation
        if (!age || age < 1 || age > 120) {
            showAlert(insuranceAlert, 'Age must be between 1 and 120.', 'danger');
            return;
        }
        if (!budget || budget < 0) {
            showAlert(insuranceAlert, 'Monthly budget must be a non-negative number.', 'danger');
            return;
        }

        showLoading(btn);
        try {
            const result = await InsuranceAPI.getRecommendation(user.user_id, age, budget, needsCriticalIllness, needsMaternity, needsAccident);

            if (!result.top || result.top.length === 0) {
                showAlert(insuranceAlert,
                    result.reason || 'No eligible insurance plans found for your profile.',
                    'info');
                resultsSection.classList.add('hidden');
                return;
            }

            showAlert(insuranceAlert,
                `Found ${result.top.length} matching plans! (Request ID: ${result.request_id})`,
                'success');

            renderResults(result.top);
            resultsSection.classList.remove('hidden');
            resultsSection.style.display = '';
            const emptyResults = document.getElementById('emptyResults');
            if (emptyResults) emptyResults.style.display = 'none';
        } catch (error) {
            showAlert(insuranceAlert, error.message, 'danger');
        } finally {
            hideLoading(btn);
        }
    });

    function renderResults(plans) {
        const rankColors = ['gold', 'silver', 'bronze', '', ''];

        resultsList.innerHTML = plans.map((plan, idx) => `
            <div class="rank-card" style="flex-direction: column; align-items: stretch; gap: 1rem;">
                <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
                    <div class="rank-number ${rankColors[idx]}">${plan.rank}</div>
                    <div class="rank-info" style="flex:1;">
                        <h4>${plan.plan_name} <span class="text-muted" style="font-weight: 400; font-size: 0.9em;">| ₹${plan.premium.toLocaleString()}/mo</span></h4>
                        <p style="margin-bottom: 0.5rem;">${plan.type}</p>
                        
                        <!-- Eligibility Criteria Columns (Requested by User) -->
                        <div style="display:inline-flex; gap:1.5rem; background: var(--border-color); padding: 4px 12px; border-radius: 4px; font-size: 0.85rem; margin-top: 4px;">
                            <span><strong>Eligibility:</strong> Age ${plan.min_age} - ${plan.max_age}</span>
                            <span><strong>Co-Pay:</strong> ${plan.co_pay}%</span>
                        </div>
                    </div>
                    <div class="rank-details" style="text-align: right;">
                        <div class="score" style="font-size: 1.5rem; color: var(--primary);">${(plan.score * 100).toFixed(1)}<span style="font-size: 1rem;">%</span></div>
                    </div>
                </div>
                <div style="background-color: var(--surface-hover); padding: 1rem; border-radius: 8px;">
                    <div class="score-bar-container" style="margin-bottom: 0.5rem; height: 6px;">
                        <div class="score-bar" style="width: ${(plan.score * 100).toFixed(0)}%"></div>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem;">
                        ${(plan.explanations || []).map(exp => {
                            let badgeClass = 'primary';
                            if (['check_circle', 'verified', 'health_and_safety', 'workspace_premium', 'pregnant_woman', 'personal_injury', 'payments'].includes(exp.icon)) badgeClass = 'success';
                            if (['warning'].includes(exp.icon)) badgeClass = 'warning';
                            if (['error'].includes(exp.icon)) badgeClass = 'danger';
                            if (['info'].includes(exp.icon)) badgeClass = 'info';
                            
                            return `<span class="badge badge-${badgeClass}" style="display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; font-weight: 500;">
                                <span class="material-symbols-outlined" style="font-size: 16px;">${exp.icon}</span>
                                ${exp.text}
                            </span>`;
                        }).join('')}
                    </div>
                    <div class="text-xs text-muted" style="margin-top: 0.8rem; display: flex; justify-content: space-between;">
                        <span>Max Coverage: <strong>₹${plan.coverage.toLocaleString()}</strong></span>
                        <span>Type: ${plan.type}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }
});
