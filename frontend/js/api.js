/**
 * ValueTrack — API Wrapper
 * Centralized Fetch API helper for all backend calls.
 */

const API_BASE = 'http://127.0.0.1:5000/api';

/**
 * Generic API call wrapper with error handling.
 * @param {string} endpoint - API endpoint (e.g., '/auth/login')
 * @param {object} options - Fetch options override
 * @returns {Promise<object>} JSON response
 */
async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;

    const defaults = {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'  // send cookies for auth
    };

    const config = { ...defaults, ...options };

    // Don't set Content-Type for FormData (file upload)
    if (config.body instanceof FormData) {
        delete config.headers['Content-Type'];
    }

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}`);
        }

        return data;
    } catch (error) {
        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
            throw new Error('Cannot connect to server. Make sure the backend is running on port 5000.');
        }
        throw error;
    }
}

// ---- Auth API ----
const AuthAPI = {
    register: (name, email, password) =>
        apiCall('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ name, email, password })
        }),

    login: (email, password) =>
        apiCall('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        })
};

// ---- Loans API ----
const LoansAPI = {
    create: (userId, principal, annualInterestRate, tenureMonths, startDate) =>
        apiCall('/loans', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                principal,
                annual_interest_rate: annualInterestRate,
                tenure_months: tenureMonths,
                start_date: startDate
            })
        }),

    getSchedule: (loanId) =>
        apiCall(`/loans/${loanId}/schedule`)
};

// ---- Expenses API ----
const ExpensesAPI = {
    create: (userId, category, amount, expenseDate, description) =>
        apiCall('/expenses', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                category,
                amount,
                expense_date: expenseDate,
                description
            })
        }),

    import: (userId, file) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', userId);

        return apiCall('/expenses/import', {
            method: 'POST',
            body: formData
        });
    },

    list: (userId, month, year) => {
        let params = `user_id=${userId}`;
        if (month) params += `&month=${month}`;
        if (year) params += `&year=${year}`;
        return apiCall(`/expenses?${params}`);
    }
};

// ---- Insurance API ----
const InsuranceAPI = {
    request: (userId, age, preExisting, annualBudget) =>
        apiCall('/insurance/request', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                age,
                pre_existing_condition: preExisting,
                annual_budget: annualBudget
            })
        }),

    getResult: (requestId) =>
        apiCall(`/insurance/result/${requestId}`)
};

// ---- Dashboard API ----
const DashboardAPI = {
    get: (userId) =>
        apiCall(`/dashboard?user_id=${userId}`)
};

// ---- Utility: show/hide loading ----
function showLoading(btn) {
    if (btn) {
        btn.dataset.originalText = btn.innerHTML;
        btn.innerHTML = '<span class="spinner"></span> Loading...';
        btn.disabled = true;
    }
}

function hideLoading(btn) {
    if (btn && btn.dataset.originalText) {
        btn.innerHTML = btn.dataset.originalText;
        btn.disabled = false;
    }
}

// ---- Utility: show alert message ----
function showAlert(container, message, type = 'danger') {
    const icon = type === 'success' ? 'check_circle' : type === 'info' ? 'info' : 'error';
    container.innerHTML = `
        <div class="alert alert-${type}">
            <span class="material-symbols-outlined">${icon}</span>
            ${message}
        </div>
    `;
    // Auto-remove after 5 seconds for success
    if (type === 'success') {
        setTimeout(() => { container.innerHTML = ''; }, 5000);
    }
}

// ---- Utility: get logged-in user ----
function getUser() {
    const user = localStorage.getItem('valuetrack_user');
    return user ? JSON.parse(user) : null;
}

function requireAuth() {
    const user = getUser();
    if (!user) {
        window.location.href = 'index.html';
        return null;
    }
    return user;
}

function logout() {
    localStorage.removeItem('valuetrack_user');
    window.location.href = 'index.html';
}
