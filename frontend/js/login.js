const loginForm = document.getElementById("loginForm");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const errorBox = document.getElementById("loginError");

function showError(message) {
    if (errorBox) {
        errorBox.textContent = message;
        errorBox.hidden = false;
        return;
    }

    alert(message);
}

function hideError() {
    if (errorBox) {
        errorBox.hidden = true;
        errorBox.textContent = "";
    }
}

if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        hideError();

        const email = emailInput.value.trim();
        const password = passwordInput.value;

        try {
            const data = await request("/auth/login", "POST", { email, password });

            localStorage.setItem("access_token", data.token.access_token);
            localStorage.setItem("user", JSON.stringify(data.user));
            localStorage.setItem("role", data.user.role);

            if (data.user.role === "admin") {
                window.location.href = "admin.html";
                return;
            }

            if (data.user.role === "master") {
                window.location.href = "schedule.html";
                return;
            }

            window.location.href = "../index.html";
        } catch (error) {
            console.error("Login error:", error);
            const fallbackMessage = error?.message || "Помилка з'єднання з сервером. Перевірте, чи запущено API.";
            showError(fallbackMessage);
        }
    });
}
