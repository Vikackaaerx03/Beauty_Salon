document.addEventListener("DOMContentLoaded", async () => {
    const serviceSelect = document.getElementById("serviceSelect");
    const masterSelect = document.getElementById("masterSelect");
    const timeslotSelect = document.getElementById("timeslotSelect");
    const bookingForm = document.getElementById("bookingForm");
    const bookingHelp = document.getElementById("bookingHelp");
    const masterPreview = document.getElementById("masterPreview");

    let services = [];
    let masters = [];
    let schedules = [];
    const ratingByMaster = new Map();

    const escapeHtml = (value) =>
        String(value ?? "").replace(/[&<>"']/g, (char) => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        }[char]));

    const stars = (rating) => {
        const value = Math.max(0, Math.min(5, Math.round(Number(rating) || 0)));
        return `${"★".repeat(value)}${"☆".repeat(5 - value)}`;
    };

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

    const serviceNameById = (serviceId) => services.find((service) => String(service.id) === String(serviceId))?.name || "";

    const masterMatchesService = (master, serviceId) => {
        if (!serviceId) return true;
        return (master.services_offered || []).map(String).includes(String(serviceId));
    };

    const getFilteredMasters = () => {
        const selectedServiceId = serviceSelect?.value || "";
        return masters.filter((master) => masterMatchesService(master, selectedServiceId));
    };

    const getMasterSlots = (masterId) => schedules.filter((slot) => String(slot.master_id) === String(masterId));

    const isPastSlot = (slot) => {
        const start = new Date(slot.start);
        return !Number.isNaN(start.getTime()) && start.getTime() < Date.now();
    };

    const formatSlot = (slot) => {
        const date = new Date(slot.start);
        return date.toLocaleString("uk-UA", {
            day: "2-digit",
            month: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const setHelp = (text, variant = "info") => {
        if (!bookingHelp) return;
        bookingHelp.dataset.variant = variant;
        bookingHelp.textContent = text;
    };

    const renderMasterPreview = (masterId) => {
        if (!masterPreview) return;

        const master = masters.find((item) => String(item.id) === String(masterId));
        if (!master) {
            masterPreview.innerHTML = `<div class="master-preview__empty">Оберіть майстра, щоб побачити рейтинг і послуги.</div>`;
            return;
        }

        const rating = Number(ratingByMaster.get(String(master.id)) ?? master.rating ?? 0);
        const servicesList = (master.services_offered || []).map((serviceId) => serviceNameById(serviceId)).filter(Boolean);
        const avatarSrc = master.avatar ? (master.avatar.startsWith("assets/") ? `../${master.avatar}` : `../assets/images/${master.avatar}`) : buildAvatar(master.name, master.id);

        masterPreview.innerHTML = `
            <div class="master-preview__card">
                <img class="master-preview__avatar" src="${escapeHtml(avatarSrc)}" alt="${escapeHtml(master.name)}">
                <div class="master-preview__content">
                    <div class="master-preview__top">
                        <strong>${escapeHtml(master.name)}</strong>
                        <span class="master-preview__rating">${stars(rating)} ${rating.toFixed(1)}</span>
                    </div>
                    <div class="master-preview__services">
                        ${servicesList.length ? servicesList.map((service) => `<span>${escapeHtml(service)}</span>`).join("") : "<span>Послуги ще не вказані</span>"}
                    </div>
                </div>
            </div>
        `;
    };

    const renderServiceOptions = () => {
        if (!serviceSelect) return;
        const options = services.map((service) => `<option value="${escapeHtml(service.id)}">${escapeHtml(service.name)} (${escapeHtml(service.price)} грн)</option>`).join("");
        serviceSelect.innerHTML = `<option value="">Оберіть послугу</option>${options}`;
    };

    const renderMasterOptions = () => {
        if (!masterSelect) return;

        const selectedServiceId = serviceSelect?.value || "";
        const list = getFilteredMasters();
        const currentMasterValue = masterSelect.value;

        masterSelect.innerHTML = `
            <option value="">Оберіть майстра</option>
            ${list.map((master) => {
                const rating = Number(ratingByMaster.get(String(master.id)) ?? master.rating ?? 0);
                const matchedServices = (master.services_offered || []).map((serviceId) => serviceNameById(serviceId)).filter(Boolean).slice(0, 3).join(", ");
                return `
                    <option value="${escapeHtml(master.id)}" ${String(currentMasterValue) === String(master.id) ? "selected" : ""}>
                        ${escapeHtml(master.name)} • ${stars(rating)} ${rating.toFixed(1)}${matchedServices ? ` • ${escapeHtml(matchedServices)}` : ""}${selectedServiceId ? ` • ${escapeHtml(serviceNameById(selectedServiceId))}` : ""}
                    </option>
                `;
            }).join("")}
        `;

        if (currentMasterValue && !list.some((master) => String(master.id) === String(currentMasterValue))) {
            masterSelect.value = "";
        }

        if (!selectedServiceId) {
            setHelp("Після вибору послуги список майстрів автоматично відфільтрується.", "info");
            renderMasterPreview("");
            return;
        }

        if (list.length === 0) {
            setHelp("Під цю послугу поки немає доступних майстрів.", "warning");
            renderMasterPreview("");
            return;
        }

        setHelp(`Під обрану послугу знайдено ${list.length} майстрів. Рейтинг показано прямо в списку.`, "info");
        renderMasterPreview(currentMasterValue);
    };

    const renderTimeslots = (masterId) => {
        if (!timeslotSelect) return;

        if (!masterId) {
            timeslotSelect.innerHTML = '<option value="">Спочатку оберіть майстра</option>';
            return;
        }

        const slots = getMasterSlots(masterId);
        if (!slots.length) {
            timeslotSelect.innerHTML = '<option value="">Немає доступних слотів</option>';
            return;
        }

        const available = slots.filter((slot) => slot.status === "free" && !slot.booking_id && !isPastSlot(slot));
        const unavailable = slots.filter((slot) => slot.status !== "free" || !!slot.booking_id || isPastSlot(slot));

        const availableOptions = available.map((slot) => `
            <option value="${escapeHtml(slot.id)}" class="slot-option slot-option--free">
                🟢 ${escapeHtml(formatSlot(slot))} • вільно
            </option>
        `).join("");

        const unavailableOptions = unavailable.map((slot) => {
            const reason = isPastSlot(slot)
                ? "минув"
                : slot.status === "booked" || slot.booking_id
                    ? "зайнято"
                    : slot.status || "недоступно";
            return `
                <option value="${escapeHtml(slot.id)}" disabled class="slot-option slot-option--disabled">
                    🔴 ${escapeHtml(formatSlot(slot))} • ${escapeHtml(reason)}
                </option>
            `;
        }).join("");

        timeslotSelect.innerHTML = `
            <option value="">Оберіть зручний час</option>
            ${availableOptions ? `<optgroup label="Доступні">${availableOptions}</optgroup>` : ""}
            ${unavailableOptions ? `<optgroup label="Недоступні">${unavailableOptions}</optgroup>` : ""}
        `;
    };

    try {
        services = await request("/services");
        renderServiceOptions();
    } catch (error) {
        console.error("Помилка завантаження послуг:", error);
    }

    try {
        const [mastersResult, feedbackResult] = await Promise.allSettled([
            request("/users/masters"),
            request("/feedback"),
        ]);

        masters = mastersResult.status === "fulfilled" && Array.isArray(mastersResult.value) ? mastersResult.value : [];
        const feedbacks = feedbackResult.status === "fulfilled" && Array.isArray(feedbackResult.value) ? feedbackResult.value : [];

        feedbacks.forEach((item) => {
            const masterId = String(item.master_id || "");
            if (!masterId) return;
            const list = ratingByMaster.get(masterId) || [];
            list.push(Number(item.rating || 0));
            ratingByMaster.set(masterId, list.filter((value) => value >= 1 && value <= 5));
        });

        const averageByMaster = new Map();
        ratingByMaster.forEach((ratings, masterId) => {
            const average = ratings.length ? ratings.reduce((sum, value) => sum + value, 0) / ratings.length : 0;
            averageByMaster.set(masterId, average);
        });
        ratingByMaster.clear();
        averageByMaster.forEach((value, key) => ratingByMaster.set(key, value));

        renderMasterOptions();
    } catch (error) {
        console.error("Помилка завантаження майстрів:", error);
    }

    try {
        schedules = await request("/schedules");
        if (masterSelect?.value) {
            renderTimeslots(masterSelect.value);
        }
    } catch (error) {
        console.error("Помилка завантаження слотів:", error);
    }

    serviceSelect?.addEventListener("change", () => {
        renderMasterOptions();
        if (masterSelect) masterSelect.value = "";
        renderMasterPreview("");
        if (timeslotSelect) {
            timeslotSelect.innerHTML = '<option value="">Спочатку оберіть майстра</option>';
        }
    });

    masterSelect?.addEventListener("change", (event) => {
        renderMasterPreview(event.target.value);
        renderTimeslots(event.target.value);
    });

    if (bookingForm) {
        bookingForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const serviceId = serviceSelect?.value;
            const masterId = masterSelect?.value;
            const timeslotId = timeslotSelect?.value;

            if (!serviceId || !masterId || !timeslotId) {
                alert("Будь ласка, оберіть послугу, майстра та час.");
                return;
            }

            const selectedSlot = schedules.find((slot) => String(slot.id) === String(timeslotId));
            if (!selectedSlot || selectedSlot.status !== "free" || selectedSlot.booking_id || isPastSlot(selectedSlot)) {
                alert("Цей час вже недоступний. Оберіть інший слот.");
                renderTimeslots(masterId);
                return;
            }

            try {
                await request("/bookings", "POST", {
                    service_id: String(serviceId),
                    master_id: String(masterId),
                    timeslot_id: String(timeslotId),
                });
                alert("Чудово! Ви успішно записані.");
                window.location.href = "profile.html";
            } catch (error) {
                console.error("Booking error:", error);
                alert(error.message || "Не вдалося створити запис.");
            }
        });
    }
});
