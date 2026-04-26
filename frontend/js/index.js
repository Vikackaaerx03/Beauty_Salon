document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("access_token");
    const userStr = localStorage.getItem("user");

    const guestButtons = document.getElementById("guestButtons");
    const userButtons = document.getElementById("userButtons");
    const adminLink = document.getElementById("adminLink");
    const navLinks = document.getElementById("navLinks");
    const bookingCtaBtn = document.getElementById("bookingCtaBtn");
    const mastersGrid = document.getElementById("homeMastersGrid");
    const sortSelect = document.getElementById("masterSortSelect");
    const masterFilterSelect = document.getElementById("masterFilterSelect");
    const serviceFilterSelect = document.getElementById("serviceFilterSelect");

    const fallbackMasters = [
        { id: "1", name: "Олена Гринчук", rating: 4.9, services_offered: ["1", "2"] },
        { id: "2", name: "Ольга Вірник", rating: 4.8, services_offered: ["2", "3"] },
        { id: "3", name: "Таня Мірошник", rating: 4.7, services_offered: ["1", "4"] },
        { id: "4", name: "Аліна Колос", rating: 4.6, services_offered: ["3", "5"] },
        { id: "5", name: "Ірина Стеценко", rating: 4.5, services_offered: ["2", "4"] },
    ];

    const fallbackServices = new Map([
        ["1", "Манікюр"],
        ["2", "Педикюр"],
        ["3", "Стрижка"],
        ["4", "Фарбування"],
        ["5", "Догляд"],
    ]);

    const escapeHtml = (value) =>
        String(value ?? "").replace(/[&<>"']/g, (char) => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        }[char]));

    const seedHash = (value) => {
        const text = String(value ?? "");
        let hash = 0;
        for (let i = 0; i < text.length; i += 1) {
            hash = (hash * 31 + text.charCodeAt(i)) >>> 0;
        }
        return hash;
    };

    const buildAvatar = (label, seed) => {
        const initials = String(label || "")
            .trim()
            .split(/\s+/)
            .slice(0, 2)
            .map((part) => part[0]?.toUpperCase() || "")
            .join("") || "BS";

        const palette = [
            ["#7d4e57", "#d99aa2"],
            ["#5c5a9e", "#b9b7f2"],
            ["#3c766f", "#9ed6cf"],
            ["#9d6c3f", "#f1c18d"],
            ["#6f4e8f", "#d2b8f0"],
        ];
        const colors = palette[seedHash(seed) % palette.length];

        const svg = `
            <svg xmlns="http://www.w3.org/2000/svg" width="220" height="220" viewBox="0 0 220 220">
                <defs>
                    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="${colors[0]}"/>
                        <stop offset="100%" stop-color="${colors[1]}"/>
                    </linearGradient>
                </defs>
                <rect width="220" height="220" rx="36" fill="url(#g)"/>
                <circle cx="110" cy="86" r="42" fill="rgba(255,255,255,0.18)"/>
                <text x="110" y="128" text-anchor="middle" font-family="Montserrat, Arial, sans-serif" font-size="58" font-weight="700" fill="#ffffff">${initials}</text>
            </svg>
        `;

        return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
    };

    const stars = (rating) => {
        const safeRating = Math.max(0, Math.min(5, Number(rating) || 0));
        return `${String.fromCodePoint(9733).repeat(Math.floor(safeRating))}${String.fromCodePoint(9734).repeat(5 - Math.floor(safeRating))}`;
    };

    const resolveAvatar = (master) => {
        const avatar = String(master?.avatar || "").trim();
        if (avatar) {
            if (/^(https?:|data:|\/|\.{1,2}\/)/.test(avatar) || avatar.startsWith("assets/")) {
                return avatar;
            }
            return `assets/images/${avatar.replace(/^\/+/, "")}`;
        }
        return buildAvatar(master?.name || "", master?.id || master?.name || "");
    };

    let user = null;
    let userRole = null;

    if (token && userStr) {
        try {
            user = JSON.parse(userStr);
            userRole = user?.role || null;
        } catch (error) {
            localStorage.removeItem("user");
            localStorage.removeItem("access_token");
            localStorage.removeItem("role");
            window.location.reload();
            return;
        }

        if (userRole === "admin") {
            window.location.href = "pages/admin.html";
            return;
        }

        if (guestButtons) guestButtons.style.display = "none";
        if (userButtons) userButtons.style.display = "flex";

        if (userButtons && !document.querySelector(".user-greeting")) {
            const greeting = document.createElement("span");
            greeting.className = "user-greeting";
            greeting.textContent = `Вітаю, ${user.name}!`;
            userButtons.prepend(greeting);
        }

        if (userRole === "client" && navLinks && !document.getElementById("profileLink")) {
            const profileLink = document.createElement("a");
            profileLink.href = "pages/profile.html";
            profileLink.id = "profileLink";
            profileLink.className = "nav-account-link";
            profileLink.textContent = "Обліковий запис";
            navLinks.appendChild(profileLink);
        }

        if (userRole === "master" && navLinks && !document.getElementById("masterDashboardLink")) {
            const dashboardLink = document.createElement("a");
            dashboardLink.href = "pages/schedule.html";
            dashboardLink.id = "masterDashboardLink";
            dashboardLink.className = "nav-account-link";
            dashboardLink.textContent = "Кабінет майстра";
            navLinks.appendChild(dashboardLink);
        }
    } else {
        if (guestButtons) guestButtons.style.display = "flex";
        if (userButtons) userButtons.style.display = "none";
        if (adminLink) adminLink.style.display = "none";
    }

    const goToBooking = () => {
        if (!token) {
            alert("Будь ласка, увійдіть у систему!");
            window.location.href = "pages/login.html";
            return;
        }

        if (userRole === "client") {
            window.location.href = "pages/booking.html";
            return;
        }

        alert("Запис доступний тільки для клієнтів!");
    };

    bookingCtaBtn?.addEventListener("click", goToBooking);

    if (!mastersGrid) {
        return;
    }

    if (sortSelect && !sortSelect.value) {
        sortSelect.value = "rating";
    }

    const normalizeMasters = (list) => (Array.isArray(list) && list.length ? list : fallbackMasters);

    const filterMasters = (list, filters) => {
        const selectedMaster = String(filters.masterId || "");
        const selectedService = String(filters.serviceId || "");

        return list.filter((master) => {
            const masterMatch = !selectedMaster || String(master.id) === selectedMaster;
            const serviceMatch = !selectedService || (master.services_offered || []).map(String).includes(selectedService);
            return masterMatch && serviceMatch;
        });
    };

    const sortMasters = (list, sortBy, ratingsMap) => {
        const clone = [...list];
        if (sortBy === "name") {
            return clone.sort((a, b) => String(a.name || "").localeCompare(String(b.name || ""), "uk"));
        }
        return clone.sort((a, b) => {
            const ratingA = Number(ratingsMap.get(String(a.id)) ?? a.rating ?? 0);
            const ratingB = Number(ratingsMap.get(String(b.id)) ?? b.rating ?? 0);
            return ratingB - ratingA;
        });
    };

    const renderControls = (masters, servicesById) => {
        if (masterFilterSelect) {
            const selected = masterFilterSelect.value;
            masterFilterSelect.innerHTML = '<option value="">Усі майстри</option>' + masters
                .map((master) => `<option value="${escapeHtml(master.id)}" ${String(selected) === String(master.id) ? "selected" : ""}>${escapeHtml(master.name)}</option>`)
                .join("");
        }

        if (serviceFilterSelect) {
            const selected = serviceFilterSelect.value;
            const serviceOptions = Array.from(servicesById.entries())
                .map(([id, name]) => `<option value="${escapeHtml(id)}" ${String(selected) === String(id) ? "selected" : ""}>${escapeHtml(name)}</option>`)
                .join("");
            serviceFilterSelect.innerHTML = '<option value="">Усі послуги</option>' + serviceOptions;
        }
    };

    const renderMasters = (masters, servicesById, ratingsMap) => {
        const sortBy = sortSelect?.value || "rating";
        const selectedMasterId = masterFilterSelect?.value || "";
        const selectedServiceId = serviceFilterSelect?.value || "";

        const normalized = filterMasters(sortMasters(masters, sortBy, ratingsMap), {
            masterId: selectedMasterId,
            serviceId: selectedServiceId,
        });

        if (normalized.length === 0) {
            mastersGrid.innerHTML = '<p class="loading-text">За обраними фільтрами майстрів немає.</p>';
            return;
        }

        mastersGrid.innerHTML = normalized.map((master) => {
            const rating = Number(ratingsMap.get(String(master.id)) ?? master.rating ?? 0);
            const serviceNames = (master.services_offered || [])
                .map((serviceId) => servicesById.get(String(serviceId)))
                .filter(Boolean)
                .slice(0, 3);

            return `
                <article class="home-master-card">
                    <img class="home-master-card__avatar" src="${escapeHtml(resolveAvatar(master))}" alt="${escapeHtml(master.name)}">
                    <div class="home-master-card__info">
                        <p class="home-master-card__role">Майстер</p>
                        <h3 class="home-master-card__name">${escapeHtml(master.name)}</h3>
                        <div class="home-master-card__meta">
                            <p class="master-meta"><span class="stars">${stars(rating)}</span> ${rating.toFixed(1)}</p>
                            <p class="master-meta">${serviceNames.length ? `${serviceNames.length} послуги` : "Індивідуальний підхід"}</p>
                        </div>
                        <div class="master-services">
                            ${
                                serviceNames.length
                                    ? serviceNames.map((serviceName) => `<span class="master-service-chip">${escapeHtml(serviceName)}</span>`).join("")
                                    : '<span class="master-service-chip">Без послуг</span>'
                            }
                        </div>
                    </div>
                </article>
            `;
        }).join("");
    };

    try {
        const [mastersResult, servicesResult, feedbackResult] = await Promise.allSettled([
            request("/users/masters"),
            request("/services"),
            request("/feedback"),
        ]);

        const masters = normalizeMasters(mastersResult.status === "fulfilled" ? mastersResult.value : null);
        const services = servicesResult.status === "fulfilled" && Array.isArray(servicesResult.value) ? servicesResult.value : [];
        const feedbacks = feedbackResult.status === "fulfilled" && Array.isArray(feedbackResult.value) ? feedbackResult.value : [];

        const servicesById = new Map(fallbackServices);
        services.forEach((service) => {
            servicesById.set(String(service.id), service.name);
        });

        const ratingsMap = new Map();
        feedbacks.forEach((item) => {
            const masterId = String(item.master_id || "");
            if (!masterId) return;
            const list = ratingsMap.get(masterId) || [];
            const rating = Number(item.rating || 0);
            if (rating >= 1 && rating <= 5) list.push(rating);
            ratingsMap.set(masterId, list);
        });

        const averageMap = new Map();
        ratingsMap.forEach((ratings, masterId) => {
            const average = ratings.length ? ratings.reduce((sum, value) => sum + value, 0) / ratings.length : 0;
            averageMap.set(masterId, average);
        });

        renderControls(masters, servicesById);
        renderMasters(masters, servicesById, averageMap);

        const rerender = () => renderMasters(masters, servicesById, averageMap);
        sortSelect?.addEventListener("change", rerender);
        masterFilterSelect?.addEventListener("change", rerender);
        serviceFilterSelect?.addEventListener("change", rerender);
    } catch (error) {
        console.error("Failed to render masters:", error);
        mastersGrid.innerHTML = '<p class="error-text">Не вдалося завантажити список майстрів.</p>';
    }
});
