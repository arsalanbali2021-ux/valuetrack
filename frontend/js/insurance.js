/**
 * ValueTrack — Insurance Page Logic
 * Eligibility form + ranked top-5 results display.
 */

document.addEventListener('DOMContentLoaded', () => {
    const user = requireAuth();
    if (!user) return;

    const userNameEl = document.getElementById('userName');
    if (userNameEl) userNameEl.textContent = user.name;

    const insuranceForm = document.getElementById('insuranceForm');
    const insuranceAlert = document.getElementById('insuranceAlert');
    const resultsSection = document.getElementById('resultsSection');
    const resultsList = document.getElementById('resultsList');

    insuranceForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = insuranceForm.querySelector('button[type="submit"]');

        const age = parseInt(document.getElementById('age').value);
        const preExisting = document.getElementById('preExisting').checked;
        const budget = parseFloat(document.getElementById('budget').value);

        // Validation
        if (!age || age < 1 || age > 120) {
            showAlert(insuranceAlert, 'Age must be between 1 and 120.', 'danger');
            return;
        }
        if (!budget || budget < 0) {
            showAlert(insuranceAlert, 'Annual budget must be a non-negative number.', 'danger');
            return;
        }

        showLoading(btn);
        try {
            const result = await InsuranceAPI.request(user.user_id, age, preExisting, budget);

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
        } catch (error) {
            showAlert(insuranceAlert, error.message, 'danger');
        } finally {
            hideLoading(btn);
        }
    });

    function renderResults(plans) {
        const rankColors = ['gold', 'silver', 'bronze', '', ''];

        resultsList.innerHTML = plans.map((plan, idx) => `
            <div class="rank-card">
                <div class="rank-number ${rankColors[idx]}">${plan.rank}</div>
                <div class="rank-info">
                    <h4>${plan.provider}</h4>
                    <p>${plan.plan_name}</p>
                </div>
                <div style="flex:1;">
                    <div class="score-bar-container">
                        <div class="score-bar" style="width: ${(plan.score * 100).toFixed(0)}%"></div>
                    </div>
                    <div class="text-xs text-muted mt-1">
                        Coverage: ₹${plan.coverage.toLocaleString()}
                    </div>
                </div>
                <div class="rank-details">
                    <div class="score">${(plan.score * 100).toFixed(1)}%</div>
                    <div class="premium">₹${plan.premium.toLocaleString()}/yr</div>
                </div>
            </div>
        `).join('');
    }
});
