document.addEventListener("DOMContentLoaded", async () => {
    const userStr = localStorage.getItem("user");
    const token = localStorage.getItem("access_token");

    if (!token || !userStr) {
        window.location.href = "login.html";
        return;
    }

    let user = null;
    try {
        user = JSON.parse(userStr);
    } catch (error) {
        window.location.href = "login.html";
        return;
    }

    if (user?.role !== "master") {
        alert("Доступ заборонено. Тільки для майстрів.");
        window.location.href = "../index.html";
        return;
    }

    const dashboardTitle = document.getElementById("masterDashboardTitle");
    const dashboardSubtitle = document.getElementById("masterDashboardSubtitle");
    const profileForm = document.getElementById("masterProfileForm");
    const nameInput = document.getElementById("masterName");
    const emailInput = document.getElementById("masterEmail");
    const avatarPreview = document.getElementById("masterAvatarPreview");
    const avatarFileInput = document.getElementById("masterAvatarFile");
    const servicesSelect = document.getElementById("masterServices");
    const bookingsList = document.getElementById("masterBookingsList");
    const bookingsFilter = document.getElementById("masterBookingFilter");
    const reviewsList = document.getElementById("masterReviewsList");
    const servicesBadge = document.getElementById("masterServicesBadge");
    const ratingSummary = document.getElementById("masterRatingSummary");

    const avatarMap = new Map([
        ["Олена Гринюк", "../assets/images/icon_1.jpg"],
        ["Марія Коваль", "../assets/images/icon_2.jpg"],
        ["Анна Мельник", "../assets/images/icon_3.jpg"],
        ["Іван Шевченко", "../assets/images/icon_4.jpg"],
        ["Дмитро Савчук", "../assets/images/icon_5.jpg"],
    ]);

    const serviceChoices = [];
    let bookingsCache = [];
    let feedbackCache = [];
    let selectedAvatarFile = null;

    const escapeHtml = (value) =>
        String(value ?? "").replace(/[&<>"']/g, (char) => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        }[char]));

    const makeInitialsAvatar = (label) => {
        const initials = String(label || "")
            .trim()
            .split(/\s+/)
            .slice(0, 2)
            .map((part) => part[0]?.toUpperCase() || "")
            .join("") || "BS";

        const svg = `
            <svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 160 160">
                <defs>
                    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#7d4e57"/>
                        <stop offset="100%" stop-color="#d99aa2"/>
                    </linearGradient>
                </defs>
                <rect width="160" height="160" rx="28" fill="url(#g)"/>
                <circle cx="80" cy="62" r="30" fill="rgba(255,255,255,0.18)"/>
                <text x="80" y="98" text-anchor="middle" font-family="Montserrat, Arial, sans-serif" font-size="42" font-weight="700" fill="#ffffff">${initials}</text>
            </svg>
        `;

        return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
    };

    const resolveAvatar = (master) => {
        const avatar = String(master?.avatar || "").trim();
        if (avatar) {
            if (avatar.startsWith("assets/")) return `../${avatar}`;
            if (avatar.startsWith("../") || avatar.startsWith("/") || avatar.startsWith("http")) return avatar;
            return `../assets/images/${avatar}`;
        }

        const name = String(master?.name || "").trim();
        if (avatarMap.has(name)) {
            return avatarMap.get(name);
        }

        return "../assets/images/icon_5.jpg";
    };

    const avatarStars = (rating) => {
        const value = Math.max(0, Math.min(5, Number(rating) || 0));
        return "★".repeat(Math.floor(value)) + "☆".repeat(5 - Math.floor(value));
    };

    const avatarStarsSafe = (rating) => {
        const value = Math.max(0, Math.min(5, Number(rating) || 0));
        return `${String.fromCodePoint(9733).repeat(Math.floor(value))}${String.fromCodePoint(9734).repeat(5 - Math.floor(value))}`;
    };

    const statusLabel = (status) => {
        const value = String(status || "pending").toLowerCase();
        if (value === "completed") return "Виконано";
        if (value === "canceled") return "Скасовано";
        if (value === "confirmed") return "Підтверджено";
        return "В очікуванні";
    };

    const statusClass = (status) => {
        const value = String(status || "pending").toLowerCase();
        if (value === "completed") return "status-completed";
        if (value === "canceled") return "status-canceled";
        if (value === "confirmed") return "status-confirmed";
        return "status-pending";
    };

    const paymentLabel = (status) => {
        const value = String(status || "unpaid").toLowerCase();
        if (value === "paid") return "Оплачено";
        if (value === "refunded") return "Повернено";
        return "Не оплачено";
    };

    const paymentClass = (status) => {
        const value = String(status || "unpaid").toLowerCase();
        if (value === "paid") return "status-confirmed";
        if (value === "refunded") return "status-canceled";
        return "status-pending";
    };

    const updateLocalUser = (updatedFields) => {
        user = { ...user, ...updatedFields };
        localStorage.setItem("user", JSON.stringify(user));
        localStorage.setItem("role", user.role);
    };

    const renderAvatar = () => {
        if (avatarPreview) {
            avatarPreview.src = resolveAvatar(user);
        }
    };

    const renderServicesBadge = () => {
        if (!servicesBadge) return;
        const names = (Array.isArray(user.services_offered) ? user.services_offered : [])
            .map((serviceId) => serviceChoices.find((service) => String(service.id) === String(serviceId))?.name)
            .filter(Boolean);
        servicesBadge.textContent = names.length ? names.join(", ") : "Послуги ще не вказані";
    };

    const renderRatingSummary = () => {
        if (!ratingSummary) return;
        const feedbackRatings = feedbackCache.map((item) => Number(item.rating || 0)).filter((value) => value >= 1 && value <= 5);
        const average = feedbackRatings.length
            ? feedbackRatings.reduce((sum, value) => sum + value, 0) / feedbackRatings.length
            : Number(user.rating || 0);
        ratingSummary.textContent = `Рейтинг: ${average.toFixed(1)} ${avatarStarsSafe(average)}`;
    };

    const renderBookings = () => {
        if (!bookingsList) return;

        const filterValue = String(bookingsFilter?.value || "all");
        const visibleBookings = bookingsCache.filter((booking) => filterValue === "all" || String(booking.status || "pending") === filterValue);

        if (!visibleBookings.length) {
            bookingsList.innerHTML = "<p class='no-data'>Записів за цим фільтром немає.</p>";
            return;
        }

        bookingsList.innerHTML = visibleBookings.map((booking) => {
            const serviceName = serviceChoices.find((service) => String(service.id) === String(booking.service_id))?.name || `Послуга #${booking.service_id || "—"}`;
            const payment = booking.payment || null;

            return `
                <article class="booking-history-item master-booking-card">
                    <div class="master-booking-card__head">
                        <img class="master-booking-card__avatar" src="${escapeHtml(makeInitialsAvatar(booking.client_name || `Клієнт #${booking.client_id || "—"}`))}" alt="${escapeHtml(booking.client_name || `Клієнт #${booking.client_id || "—"}`)}">
                        <div class="booking-header">
                            <span class="service-name">${escapeHtml(serviceName)}</span>
                            <span class="badge ${statusClass(booking.status)}">${statusLabel(booking.status)}</span>
                        </div>
                    </div>
                    <div class="booking-details">
                        <span>Клієнт: <strong>#${escapeHtml(booking.client_id || "—")}</strong></span>
                        <span>Слот: ${escapeHtml(booking.timeslot_id || "—")}</span>
                    </div>
                    <div class="master-info">
                        Оплата: <span class="badge ${paymentClass(payment?.status)}">${paymentLabel(payment?.status)}</span>
                    </div>
                    <div class="master-actions">
                        <button class="btn-row btn-row-edit" type="button" data-booking-status="completed" data-booking-id="${escapeHtml(booking.id)}">Виконано</button>
                        <button class="btn-row btn-row-delete" type="button" data-booking-status="pending" data-booking-id="${escapeHtml(booking.id)}">Не виконано</button>
                        <button class="btn-row btn-row-edit" type="button" data-booking-status="canceled" data-booking-id="${escapeHtml(booking.id)}">Скасувати</button>
                        ${payment ? `
                            <button class="btn-row btn-row-edit" type="button" data-payment-status="${payment.status === "paid" ? "unpaid" : "paid"}" data-payment-id="${escapeHtml(payment.id)}">
                                ${payment.status === "paid" ? "Не оплачено" : "Оплачено"}
                            </button>
                        ` : ""}
                    </div>
                </article>
            `;
        }).join("");

        bookingsList.querySelectorAll("[data-booking-status]").forEach((button) => {
            button.addEventListener("click", async () => {
                const bookingId = button.getAttribute("data-booking-id");
                const status = button.getAttribute("data-booking-status");
                if (!bookingId || !status) return;
                if (!confirm(`Змінити статус запису на "${statusLabel(status)}"?`)) return;
                try {
                    await request(`/bookings/${bookingId}/status`, "PATCH", { status });
                    await loadBookings();
                } catch (error) {
                    alert(error.message || "Не вдалося оновити запис.");
                }
            });
        });

        bookingsList.querySelectorAll("[data-payment-status]").forEach((button) => {
            button.addEventListener("click", async () => {
                const paymentId = button.getAttribute("data-payment-id");
                const status = button.getAttribute("data-payment-status");
                if (!paymentId || !status) return;
                if (!confirm(`Змінити статус оплати на "${paymentLabel(status)}"?`)) return;
                try {
                    await request(`/payments/${paymentId}`, "PATCH", { status });
                    await loadBookings();
                } catch (error) {
                    alert(error.message || "Не вдалося оновити оплату.");
                }
            });
        });
    };

    const renderReviews = () => {
        if (!reviewsList) return;

        if (!feedbackCache.length) {
            reviewsList.innerHTML = "<p class='no-data'>Поки що немає відгуків.</p>";
            return;
        }

        reviewsList.innerHTML = feedbackCache.map((item) => `
            <article class="master-review-card">
                <div class="master-review-card__top">
                    <span class="badge status-confirmed">${avatarStarsSafe(item.rating)} ${Number(item.rating || 0)}</span>
                    <span class="badge">${escapeHtml(item.created_at ? new Date(item.created_at).toLocaleDateString("uk-UA") : "—")}</span>
                </div>
                <div class="master-review-card__meta">
                    <div>Клієнт: <strong>#${escapeHtml(item.client_id || "—")}</strong></div>
                    <div>Коментар: ${escapeHtml(item.comment || "Без коментаря")}</div>
                </div>
            </article>
        `).join("");
    };

    const loadServices = async () => {
        const services = await request("/services");
        serviceChoices.splice(0, serviceChoices.length, ...(Array.isArray(services) ? services : []));
        if (servicesSelect) {
            const selected = new Set((user.services_offered || []).map(String));
            servicesSelect.innerHTML = serviceChoices.map((service) => `
                <option value="${escapeHtml(service.id)}" ${selected.has(String(service.id)) ? "selected" : ""}>${escapeHtml(service.name)}</option>
            `).join("");
        }
        renderServicesBadge();
    };

    const loadBookings = async () => {
        const [bookingsResult, feedbackResult] = await Promise.allSettled([
            request(`/bookings/master/${user.id}`),
            request(`/feedback?master_id=${user.id}`),
        ]);

        const bookings = bookingsResult.status === "fulfilled" && Array.isArray(bookingsResult.value) ? bookingsResult.value : [];
        const feedbacks = feedbackResult.status === "fulfilled" && Array.isArray(feedbackResult.value) ? feedbackResult.value : [];

        const bookingsWithPayments = await Promise.all(bookings.map(async (booking) => {
            try {
                const payments = await request(`/payments/booking/${booking.id}`);
                return { ...booking, payment: Array.isArray(payments) && payments.length ? payments[0] : null };
            } catch (error) {
                return { ...booking, payment: null };
            }
        }));

        bookingsCache = bookingsWithPayments;
        feedbackCache = feedbacks.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));

        const ratings = feedbackCache.map((item) => Number(item.rating || 0)).filter((value) => value >= 1 && value <= 5);
        const average = ratings.length ? ratings.reduce((sum, value) => sum + value, 0) / ratings.length : Number(user.rating || 0);
        updateLocalUser({ rating: average });

        renderRatingSummary();
        renderBookings();
        renderReviews();
    };

    const uploadAvatarFile = async () => {
        if (!avatarFileInput?.files?.length) return null;
        const formData = new FormData();
        formData.append("avatar", avatarFileInput.files[0]);
        return request(`/users/${user.id}/avatar`, "POST", formData);
    };

    const syncProfileForm = () => {
        if (nameInput) nameInput.value = user.name || "";
        if (emailInput) emailInput.value = user.email || "";
        if (avatarPreview) avatarPreview.src = resolveAvatar(user);
    };

    if (dashboardTitle) {
        dashboardTitle.textContent = `Кабінет майстра: ${user.name || "Майстер"}`;
    }

    if (dashboardSubtitle) {
        dashboardSubtitle.textContent = "Тут ти керуєш своїми записами, профілем, аватаркою, послугами та відгуками.";
    }

    bookingsFilter?.addEventListener("change", renderBookings);

    avatarFileInput?.addEventListener("change", () => {
        const file = avatarFileInput.files?.[0];
        if (!file || !avatarPreview) {
            selectedAvatarFile = null;
            return;
        }
        selectedAvatarFile = file;
        avatarPreview.src = URL.createObjectURL(file);
    });

    profileForm?.addEventListener("submit", async (event) => {
        event.preventDefault();

        const name = nameInput?.value.trim() || user.name;
        const email = emailInput?.value.trim() || user.email;
        const services_offered = Array.from(servicesSelect?.selectedOptions || []).map((option) => String(option.value));

        try {
            const updatedUser = await request(`/users/${user.id}`, "PATCH", {
                name,
                email,
                services_offered,
            });

            let avatarUpdate = null;
            if (selectedAvatarFile) {
                avatarUpdate = await uploadAvatarFile();
            }

            updateLocalUser({
                ...updatedUser,
                ...(avatarUpdate || {}),
                services_offered,
            });
            selectedAvatarFile = null;
            if (avatarFileInput) avatarFileInput.value = "";
            syncProfileForm();
            renderServicesBadge();
            renderRatingSummary();
            alert("Профіль майстра оновлено.");
        } catch (error) {
            alert(error.message || "Не вдалося оновити профіль.");
        }
    });

    syncProfileForm();
    await loadServices();
    await loadBookings();
});
