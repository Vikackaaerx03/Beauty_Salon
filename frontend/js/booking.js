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
        return `${"в…".repeat(value)}${"в†".repeat(5 - value)}`;
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
    const masterNameById = (masterId) => masters.find((master) => String(master.id) === String(masterId))?.name || `Майстер #${masterId || "—"}`;
    const slotLabel = (slot) => `${masterNameById(slot.master_id)} · ${formatSlot(slot)}`;

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
            masterPreview.innerHTML = `<div class="master-preview__empty">РћР±РµСЂС–С‚СЊ РјР°Р№СЃС‚СЂР°, С‰РѕР± РїРѕР±Р°С‡РёС‚Рё СЂРµР№С‚РёРЅРі С– РїРѕСЃР»СѓРіРё.</div>`;
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
                        ${servicesList.length ? servicesList.map((service) => `<span>${escapeHtml(service)}</span>`).join("") : "<span>РџРѕСЃР»СѓРіРё С‰Рµ РЅРµ РІРєР°Р·Р°РЅС–</span>"}
                    </div>
                </div>
            </div>
        `;
    };

    const renderServiceOptions = () => {
        if (!serviceSelect) return;
        const options = services.map((service) => `<option value="${escapeHtml(service.id)}">${escapeHtml(service.name)} (${escapeHtml(service.price)} РіСЂРЅ)</option>`).join("");
        serviceSelect.innerHTML = `<option value="">РћР±РµСЂС–С‚СЊ РїРѕСЃР»СѓРіСѓ</option>${options}`;
    };

    const renderMasterOptions = () => {
        if (!masterSelect) return;

        const selectedServiceId = serviceSelect?.value || "";
        const list = getFilteredMasters();
        const currentMasterValue = masterSelect.value;

        masterSelect.innerHTML = `
            <option value="">РћР±РµСЂС–С‚СЊ РјР°Р№СЃС‚СЂР°</option>
            ${list.map((master) => {
                const rating = Number(ratingByMaster.get(String(master.id)) ?? master.rating ?? 0);
                const matchedServices = (master.services_offered || []).map((serviceId) => serviceNameById(serviceId)).filter(Boolean).slice(0, 3).join(", ");
                return `
                    <option value="${escapeHtml(master.id)}" ${String(currentMasterValue) === String(master.id) ? "selected" : ""}>
                        ${escapeHtml(master.name)} вЂў ${stars(rating)} ${rating.toFixed(1)}${matchedServices ? ` вЂў ${escapeHtml(matchedServices)}` : ""}${selectedServiceId ? ` вЂў ${escapeHtml(serviceNameById(selectedServiceId))}` : ""}
                    </option>
                `;
            }).join("")}
        `;

        if (currentMasterValue && !list.some((master) => String(master.id) === String(currentMasterValue))) {
            masterSelect.value = "";
        }

        if (!selectedServiceId) {
            setHelp("РџС–СЃР»СЏ РІРёР±РѕСЂСѓ РїРѕСЃР»СѓРіРё СЃРїРёСЃРѕРє РјР°Р№СЃС‚СЂС–РІ Р°РІС‚РѕРјР°С‚РёС‡РЅРѕ РІС–РґС„С–Р»СЊС‚СЂСѓС”С‚СЊСЃСЏ.", "info");
            renderMasterPreview("");
            return;
        }

        if (list.length === 0) {
            setHelp("РџС–Рґ С†СЋ РїРѕСЃР»СѓРіСѓ РїРѕРєРё РЅРµРјР°С” РґРѕСЃС‚СѓРїРЅРёС… РјР°Р№СЃС‚СЂС–РІ.", "warning");
            renderMasterPreview("");
            return;
        }

        setHelp(`РџС–Рґ РѕР±СЂР°РЅСѓ РїРѕСЃР»СѓРіСѓ Р·РЅР°Р№РґРµРЅРѕ ${list.length} РјР°Р№СЃС‚СЂС–РІ. Р РµР№С‚РёРЅРі РїРѕРєР°Р·Р°РЅРѕ РїСЂСЏРјРѕ РІ СЃРїРёСЃРєСѓ.`, "info");
        renderMasterPreview(currentMasterValue);
    };

    const renderTimeslots = (masterId) => {
        if (!timeslotSelect) return;

        if (!masterId) {
            timeslotSelect.innerHTML = '<option value="">РЎРїРѕС‡Р°С‚РєСѓ РѕР±РµСЂС–С‚СЊ РјР°Р№СЃС‚СЂР°</option>';
            return;
        }

        const slots = getMasterSlots(masterId);
        if (!slots.length) {
            timeslotSelect.innerHTML = '<option value="">РќРµРјР°С” РґРѕСЃС‚СѓРїРЅРёС… СЃР»РѕС‚С–РІ</option>';
            return;
        }

        const available = slots.filter((slot) => slot.status === "free" && !slot.booking_id && !isPastSlot(slot));
        const unavailable = slots.filter((slot) => slot.status !== "free" || !!slot.booking_id || isPastSlot(slot));

        const availableOptions = available.map((slot) => `
            <option value="${escapeHtml(slot.id)}" class="slot-option slot-option--free">
                рџџў ${escapeHtml(slotLabel(slot))} вЂў РІС–Р»СЊРЅРѕ
            </option>
        `).join("");

        const unavailableOptions = unavailable.map((slot) => {
            const reason = isPastSlot(slot)
                ? "РјРёРЅСѓРІ"
                : slot.status === "booked" || slot.booking_id
                    ? "Р·Р°Р№РЅСЏС‚Рѕ"
                    : slot.status || "РЅРµРґРѕСЃС‚СѓРїРЅРѕ";
            return `
                <option value="${escapeHtml(slot.id)}" disabled class="slot-option slot-option--disabled">
                    рџ”ґ ${escapeHtml(slotLabel(slot))} вЂў ${escapeHtml(reason)}
                </option>
            `;
        }).join("");

        timeslotSelect.innerHTML = `
            <option value="">РћР±РµСЂС–С‚СЊ Р·СЂСѓС‡РЅРёР№ С‡Р°СЃ</option>
            ${availableOptions ? `<optgroup label="Р”РѕСЃС‚СѓРїРЅС–">${availableOptions}</optgroup>` : ""}
            ${unavailableOptions ? `<optgroup label="РќРµРґРѕСЃС‚СѓРїРЅС–">${unavailableOptions}</optgroup>` : ""}
        `;
    };

    try {
        services = await request("/services");
        renderServiceOptions();
    } catch (error) {
        console.error("РџРѕРјРёР»РєР° Р·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ РїРѕСЃР»СѓРі:", error);
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
        console.error("РџРѕРјРёР»РєР° Р·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ РјР°Р№СЃС‚СЂС–РІ:", error);
    }

    try {
        schedules = await request("/schedules");
        if (masterSelect?.value) {
            renderTimeslots(masterSelect.value);
        }
    } catch (error) {
        console.error("РџРѕРјРёР»РєР° Р·Р°РІР°РЅС‚Р°Р¶РµРЅРЅСЏ СЃР»РѕС‚С–РІ:", error);
    }

    serviceSelect?.addEventListener("change", () => {
        renderMasterOptions();
        if (masterSelect) masterSelect.value = "";
        renderMasterPreview("");
        if (timeslotSelect) {
            timeslotSelect.innerHTML = '<option value="">РЎРїРѕС‡Р°С‚РєСѓ РѕР±РµСЂС–С‚СЊ РјР°Р№СЃС‚СЂР°</option>';
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
                alert("Р‘СѓРґСЊ Р»Р°СЃРєР°, РѕР±РµСЂС–С‚СЊ РїРѕСЃР»СѓРіСѓ, РјР°Р№СЃС‚СЂР° С‚Р° С‡Р°СЃ.");
                return;
            }

            const selectedSlot = schedules.find((slot) => String(slot.id) === String(timeslotId));
            if (!selectedSlot || selectedSlot.status !== "free" || selectedSlot.booking_id || isPastSlot(selectedSlot)) {
                alert("Р¦РµР№ С‡Р°СЃ РІР¶Рµ РЅРµРґРѕСЃС‚СѓРїРЅРёР№. РћР±РµСЂС–С‚СЊ С–РЅС€РёР№ СЃР»РѕС‚.");
                renderTimeslots(masterId);
                return;
            }

            try {
                await request("/bookings", "POST", {
                    service_id: String(serviceId),
                    master_id: String(masterId),
                    timeslot_id: String(timeslotId),
                });
                alert("Р§СѓРґРѕРІРѕ! Р’Рё СѓСЃРїС–С€РЅРѕ Р·Р°РїРёСЃР°РЅС–.");
                window.location.href = "profile.html";
            } catch (error) {
                console.error("Booking error:", error);
                alert(error.message || "РќРµ РІРґР°Р»РѕСЃСЏ СЃС‚РІРѕСЂРёС‚Рё Р·Р°РїРёСЃ.");
            }
        });
    }
});


