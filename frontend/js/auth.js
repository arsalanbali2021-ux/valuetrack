/**
 * ValueTrack — Auth Page Logic
 * Handles login/register form switching, validation, and API calls.
 */

document.addEventListener('DOMContentLoaded', () => {
    // If already logged in, redirect based on role
    const user = getUser();
    if (user) {
        window.location.href = user.role === 'admin' ? 'admin.html' : 'dashboard.html';
        return;
    }

    // Tab switching
    const tabs = document.querySelectorAll('.auth-tab');
    const forms = document.querySelectorAll('.auth-form');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.target;
            tabs.forEach(t => t.classList.remove('active'));
            forms.forEach(f => f.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(target).classList.add('active');
        });
    });

    // Login form
    const loginForm = document.getElementById('loginForm');
    const loginAlert = document.getElementById('loginAlert');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = loginForm.querySelector('button[type="submit"]');
        const email = document.getElementById('loginEmail').value.trim();
        const password = document.getElementById('loginPassword').value;

        if (!email || !password) {
            showAlert(loginAlert, 'Please fill in all fields.', 'danger');
            return;
        }

        showLoading(btn);
        try {
            const result = await AuthAPI.login(email, password);
            // Store user info
            localStorage.setItem('valuetrack_user', JSON.stringify(result));
            showAlert(loginAlert, 'Login successful! Redirecting...', 'success');
            const redirectUrl = result.role === 'admin' ? 'admin.html' : 'dashboard.html';
            setTimeout(() => { window.location.href = redirectUrl; }, 500);
        } catch (error) {
            showAlert(loginAlert, error.message, 'danger');
        } finally {
            hideLoading(btn);
        }
    });

    // Register form
    const registerForm = document.getElementById('registerForm');
    const registerAlert = document.getElementById('registerAlert');

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = registerForm.querySelector('button[type="submit"]');
        const name = document.getElementById('registerName').value.trim();
        const email = document.getElementById('registerEmail').value.trim();
        const password = document.getElementById('registerPassword').value;
        const confirm = document.getElementById('registerConfirm').value;

        if (!name || !email || !password) {
            showAlert(registerAlert, 'Please fill in all fields.', 'danger');
            return;
        }

        if (password.length < 6) {
            showAlert(registerAlert, 'Password must be at least 6 characters.', 'danger');
            return;
        }

        if (password !== confirm) {
            showAlert(registerAlert, 'Passwords do not match.', 'danger');
            return;
        }

        showLoading(btn);
        try {
            await AuthAPI.register(name, email, password);
            showAlert(registerAlert, 'Registration successful! You can now login.', 'success');
            // Switch to login tab
            setTimeout(() => {
                tabs[0].click();
                document.getElementById('loginEmail').value = email;
            }, 1500);
        } catch (error) {
            showAlert(registerAlert, error.message, 'danger');
        } finally {
            hideLoading(btn);
        }
    });
});
