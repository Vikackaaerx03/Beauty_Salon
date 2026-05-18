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

window.getBookingDateValue = function(booking) {
    const candidates = [
        booking?.timeslot_start,
        booking?.timeslot_end,
        booking?.start,
        booking?.scheduled_start,
        booking?.schedule_start,
        booking?.booking_date,
        booking?.created_at,
        booking?.updated_at,
    ];

    for (const value of candidates) {
        if (!value) continue;
        const date = new Date(value);
        if (!Number.isNaN(date.getTime())) return date;
    }

    return null;
};

window.getBookingTimeLabel = function(booking) {
    const start = booking?.timeslot_start ? new Date(booking.timeslot_start) : null;
    const end = booking?.timeslot_end ? new Date(booking.timeslot_end) : null;
    const hasStart = start && !Number.isNaN(start.getTime());
    const hasEnd = end && !Number.isNaN(end.getTime());

    if (hasStart && hasEnd) {
        return `${start.toLocaleString("uk-UA", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        })} - ${end.toLocaleString("uk-UA", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        })}`;
    }

    if (hasStart) {
        return start.toLocaleString("uk-UA", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    if (booking?.created_at) {
        const created = new Date(booking.created_at);
        if (!Number.isNaN(created.getTime())) {
            return created.toLocaleString("uk-UA", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
        }
    }

    return "—";
};

window.getBookingDisplayStatus = function(booking) {
    const status = String(booking?.status || "pending").trim().toLowerCase();
    if (status !== "pending") return status;

    const slotDate = booking?.timeslot_end
        ? new Date(booking.timeslot_end)
        : booking?.timeslot_start
            ? new Date(booking.timeslot_start)
            : window.getBookingDateValue?.(booking);
    if (slotDate && slotDate.getTime() < Date.now()) {
        return "expired";
    }

    return status;
};

window.getBookingStatusLabel = function(status) {
    const value = String(status || "pending").trim().toLowerCase();
    if (value === "completed") return "Виконано";
    if (value === "confirmed") return "Підтверджено";
    if (value === "expired") return "Прострочено";
    if (value === "canceled") return "Скасовано";
    if (value === "deleted") return "Видалено";
    if (value === "archived") return "В архіві";
    return "В очікуванні";
};

window.getBookingStatusClass = function(status) {
    const value = String(status || "pending").trim().toLowerCase();
    if (value === "completed") return "status-completed";
    if (value === "confirmed") return "status-confirmed";
    if (value === "expired") return "status-expired";
    if (value === "canceled") return "status-canceled";
    if (value === "deleted") return "status-canceled";
    if (value === "archived") return "status-confirmed";
    return "status-pending";
};
