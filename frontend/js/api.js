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
            throw new Error(data.message || data.error || `HTTP ${response.status}`);
        }

        if (data && data.status === 'success' && data.data !== undefined) {
            return data.data;
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
        }),

    setBudget: (userId, budget) =>
        apiCall('/auth/budget', {
            method: 'PUT',
            body: JSON.stringify({ user_id: userId, monthly_budget: budget })
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
    create: (userId, category, amount, expenseDate, description, isFixed = false) =>
        apiCall('/expenses', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                category,
                amount,
                expense_date: expenseDate,
                description,
                is_fixed: isFixed
            })
        }),

    list: (userId, month, year) => {
        let params = `user_id=${userId}`;
        if (month) params += `&month=${month}`;
        if (year) params += `&year=${year}`;
        return apiCall(`/expenses?${params}`);
    }
};

// ---- Insurance API ----
const InsuranceAPI = {
    // source: 'all' (every plan) or 'irdai' (only plans linked to an IRDAI-registered product)
    getRecommendation: (userId, age, monthlyBudget, needsCriticalIllness, needsMaternity, needsAccident, source = 'all') =>
        apiCall('/insurance/request', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                age: age,
                monthly_budget: monthlyBudget,
                needs_critical_illness: needsCriticalIllness,
                needs_maternity: needsMaternity,
                needs_accident: needsAccident,
                source: source
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

// ---- Admin API ----
const AdminAPI = {
    // Insurance CRUD
    getInsurance: (userId) =>
        apiCall(`/admin/insurance?user_id=${userId}`),

    createInsurance: (data, userId) =>
        apiCall(`/admin/insurance?user_id=${userId}`, {
            method: 'POST',
            body: JSON.stringify(data)
        }),

    updateInsurance: (planId, data, userId) =>
        apiCall(`/admin/insurance/${planId}?user_id=${userId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        }),

    deleteInsurance: (planId, userId) =>
        apiCall(`/admin/insurance/${planId}?user_id=${userId}`, {
            method: 'DELETE'
        }),

    // Settings
    getSettings: (userId) =>
        apiCall(`/admin/settings?user_id=${userId}`),

    updateSettings: (settings, userId) =>
        apiCall(`/admin/settings?user_id=${userId}`, {
            method: 'PUT',
            body: JSON.stringify({ settings, user_id: userId })
        }),

    // Categories
    getCategories: (userId) =>
        apiCall(`/admin/categories?user_id=${userId}`),

    createCategory: (data, userId) =>
        apiCall(`/admin/categories?user_id=${userId}`, {
            method: 'POST',
            body: JSON.stringify(data)
        }),

    updateCategory: (catId, data, userId) =>
        apiCall(`/admin/categories/${catId}?user_id=${userId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        }),

    deleteCategory: (catId, userId) =>
        apiCall(`/admin/categories/${catId}?user_id=${userId}`, {
            method: 'DELETE'
        }),

    // Users
    getUsers: (userId) =>
        apiCall(`/admin/users?user_id=${userId}`),

    // IRDAI catalogue — pass a File (saved page / CSV) or a string (pasted rows)
    importIrdai: (fileOrText, userId) => {
        if (fileOrText instanceof File) {
            const form = new FormData();
            form.append('file', fileOrText);
            return apiCall(`/admin/irdai/import?user_id=${userId}`, { method: 'POST', body: form });
        }
        return apiCall(`/admin/irdai/import?user_id=${userId}`, {
            method: 'POST',
            body: JSON.stringify({ text: fileOrText })
        });
    },

    getIrdaiProducts: (userId, { q = '', type = '', limit = 25, offset = 0 } = {}) => {
        const params = new URLSearchParams({ user_id: userId, q, type, limit, offset });
        return apiCall(`/admin/irdai/products?${params}`);
    }
};

// ---- Utility: escape text before putting it into HTML ----
function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ---- Utility: check admin role ----
function isAdmin() {
    const user = getUser();
    return user && user.role === 'admin';
}

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
