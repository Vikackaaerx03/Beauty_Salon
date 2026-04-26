async function request(endpoint, method = "GET", body = null) {
    const token = localStorage.getItem("access_token");
    const url = `http://127.0.0.1:8000${endpoint}`;

    const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
    const headers = isFormData ? {} : { "Content-Type": "application/json" };
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const config = { method, headers };
    if (body) config.body = isFormData ? body : JSON.stringify(body);

    try {
        const response = await fetch(url, config);

        if (response.status === 204) return null;

        const text = await response.text();
        let data = null;
        try {
            data = text ? JSON.parse(text) : null;
        } catch (e) {
            data = { detail: text };
        }

        if (!response.ok) {
            const error = new Error(typeof data?.detail === "string" ? data.detail : "Помилка валідації");
            error.status = response.status;
            error.detail = data?.detail;
            throw error;
        }
        return data;
    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
}

window.logout = function() {
    localStorage.clear();
    const path = window.location.pathname.includes("/pages/") ? "../index.html" : "index.html";
    window.location.href = path;
};
