const loginForm = document.getElementById('loginForm');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const errorBox = document.getElementById('loginError');

function showError(message) {
    if (errorBox) {
        errorBox.textContent = message;
        errorBox.style.display = 'block';
    } else {
        alert(message);
    }
}

function hideError() {
    if (errorBox) {
        errorBox.style.display = 'none';
        errorBox.textContent = '';
    }
}

if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();

        const email = emailInput.value.trim();
        const password = passwordInput.value;

        try {
            const response = await fetch("http://127.0.0.1:8000/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (!response.ok) {
                showError(data.detail || "Невірний email або пароль");
                return;
            }

            localStorage.setItem("access_token", data.token.access_token);
            localStorage.setItem("user", JSON.stringify(data.user)); 
            localStorage.setItem("role", data.user.role);

            const role = data.user.role;

            if (role === 'admin') {
                window.location.href = "admin.html"; 
            } else if (role === 'master') {
                window.location.href = "masters.html"; 
            } else {
                window.location.href = "../index.html"; 
            }
            
        } catch (error) {
            console.error("Login error:", error);
            showError("Помилка з'єднання з сервером. Перевірте, чи запущено API.");
        }
    });
}