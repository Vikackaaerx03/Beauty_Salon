const registerForm = document.getElementById('registerForm');
const nameInput = document.getElementById('name');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const errorBox = document.getElementById('registerError');

function showRegisterError(message) {
    if (errorBox) {
        errorBox.textContent = message;
        errorBox.style.display = 'block';
    } else {
        alert(message);
    }
}

function hideRegisterError() {
    if (errorBox) errorBox.style.display = 'none';
}

if (registerForm) {
    nameInput.addEventListener('input', hideRegisterError);
    emailInput.addEventListener('input', hideRegisterError);
    passwordInput.addEventListener('input', hideRegisterError);

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideRegisterError();
        
        const name = nameInput.value.trim();
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        const role = document.getElementById('role').value;

        if (!name || !email || !password) {
            showRegisterError("Усі поля є обов'язковими.");
            return;
        }

        const nameParts = name.split(/\s+/); 
        if (nameParts.length < 2) {
            showRegisterError("Будь ласка, введіть своє ім'я та прізвище (мінімум два слова).");
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            showRegisterError("Будь ласка, введіть коректний email.");
            return;
        }

        if (password.length < 12) {
            showRegisterError("Пароль має містити щонайменше 12 символів.");
            return;
        }

        const data = { name, email, password, role };

        try {
            const response = await fetch("http://127.0.0.1:8000/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });
            const resData = await response.json();

            if (response.ok) {
                alert("Реєстрація успішна! Тепер увійдіть у свій акаунт.");
                window.location.href = "login.html";
            } else {
                showRegisterError(resData.detail || "Такий email вже існує.");
            }
        } catch (error) {
            showRegisterError("Помилка з'єднання з сервером.");
        }
    });
}