// Login / register page.

document.addEventListener('DOMContentLoaded', () => {
    // Already logged in? Skip straight past this page.
    const existing = getUser();
    if (existing) {
        window.location.href = existing.role === 'admin' ? 'admin.html' : 'dashboard.html';
        return;
    }

    const $ = id => document.getElementById(id);

    // Tabs
    const tabs = document.querySelectorAll('.tabs button');
    function openTab(targetId) {
        tabs.forEach(t => t.classList.toggle('active', t.dataset.target === targetId));
        document.querySelectorAll('.auth-form').forEach(f => f.classList.toggle('hidden', f.id !== targetId));
    }
    tabs.forEach(tab => tab.addEventListener('click', () => openTab(tab.dataset.target)));

    // Show / hide password
    document.querySelectorAll('.pw-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = $(btn.dataset.for);
            const show = input.type === 'password';
            input.type = show ? 'text' : 'password';
            btn.textContent = show ? 'Hide' : 'Show';
        });
    });

    // Log in
    $('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        const email = $('loginEmail').value.trim();
        const password = $('loginPassword').value;
        if (!email || !password) return showAlert($('loginAlert'), 'Enter your email and password.');

        showLoading(btn);
        try {
            const result = await AuthAPI.login(email, password);
            localStorage.setItem('valuetrack_user', JSON.stringify(result));
            window.location.href = result.role === 'admin' ? 'admin.html' : 'dashboard.html';
        } catch (error) {
            showAlert($('loginAlert'), escapeHtml(error.message));
            hideLoading(btn);
        }
    });

    // Register (same rules as the server: 8+ characters, at least one digit)
    $('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        const alertBox = $('registerAlert');
        const name = $('registerName').value.trim();
        const email = $('registerEmail').value.trim();
        const password = $('registerPassword').value;

        if (!name || !email || !password) return showAlert(alertBox, 'All fields are needed.');
        if (password.length < 8 || !/\d/.test(password)) {
            return showAlert(alertBox, 'The password needs at least 8 characters and one number.');
        }
        if (password !== $('registerConfirm').value) return showAlert(alertBox, "The two passwords don't match.");

        showLoading(btn);
        try {
            await AuthAPI.register(name, email, password);
            e.target.reset();
            openTab('loginSection');
            $('loginEmail').value = email;
            $('loginPassword').focus();
            showAlert($('loginAlert'), 'Account created. Log in with your new password.', 'success');
        } catch (error) {
            showAlert(alertBox, escapeHtml(error.message));
        } finally {
            hideLoading(btn);
        }
    });
});
