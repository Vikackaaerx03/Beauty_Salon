const registerForm = document.getElementById("registerForm");
const nameInput = document.getElementById("name");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const roleInput = document.getElementById("role");
const errorBox = document.getElementById("registerError");

function showRegisterError(message) {
    if (errorBox) {
        errorBox.textContent = message;
        errorBox.hidden = false;
        return;
    }

    alert(message);
}

function hideRegisterError() {
    if (errorBox) {
        errorBox.hidden = true;
        errorBox.textContent = "";
    }
}

if (registerForm) {
    [nameInput, emailInput, passwordInput, roleInput].forEach((input) => {
        if (input) {
            input.addEventListener("input", hideRegisterError);
            input.addEventListener("change", hideRegisterError);
        }
    });

    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        hideRegisterError();

        const name = nameInput.value.trim();
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        const role = roleInput.value;

        if (!name || !email || !password) {
            showRegisterError("Усі поля є обов'язковими.");
            return;
        }

        const nameParts = name.split(/\s+/).filter(Boolean);
        if (nameParts.length < 2) {
            showRegisterError("Будь ласка, введіть ім'я та прізвище.");
            return;
        }

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            showRegisterError("Будь ласка, введіть коректний email.");
            return;
        }

        if (password.length < 12) {
            showRegisterError("Пароль має містити щонайменше 12 символів.");
            return;
        }

        if (!["client", "master"].includes(role)) {
            showRegisterError("Реєстрація доступна тільки для клієнта або майстра.");
            return;
        }

        try {
            await request("/auth/register", "POST", { name, email, password, role });
            alert("Реєстрація успішна! Тепер увійдіть у свій акаунт.");
            window.location.href = "login.html";
        } catch (error) {
            showRegisterError(error.message || "Помилка з'єднання з сервером.");
        }
    });
}
