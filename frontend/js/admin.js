document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("access_token");
    const userRole = localStorage.getItem("role");

    if (!token || userRole !== "admin") {
        alert("Доступ заборонено. Тільки для адміністраторів.");
        window.location.href = "../index.html";
        return;
    }

    const tables = {
        bookings: document.getElementById("bookingsTable"),
        payments: document.getElementById("paymentsTable"),
        users: document.getElementById("usersTable"),
        services: document.getElementById("servicesTable"),
        schedules: document.getElementById("schedulesTable"),
        feedback: document.getElementById("feedbackTable"),
    };

    const paymentAcceptSelect = document.getElementById("paymentAcceptSelect");
    const acceptSelectedPaymentBtn = document.getElementById("acceptSelectedPaymentBtn");
    const adminLoadStatus = document.getElementById("adminLoadStatus");

    let state = {
        bookings: [],
        payments: [],
        users: [],
        services: [],
        schedules: [],
        feedback: [],
    };

    const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }[char]));

    const idSort = (a, b) => {
        const aId = Number.parseInt(String(a.id), 10);
        const bId = Number.parseInt(String(b.id), 10);
        if (Number.isFinite(aId) && Number.isFinite(bId)) return aId - bId;
        return String(a.id).localeCompare(String(b.id));
    };

    const statusLabel = (status) => {
        const map = {
            pending: '<span class="badge status-pending">Очікує</span>',
            confirmed: '<span class="badge status-confirmed">Підтверджено</span>',
            completed: '<span class="badge status-completed">Виконано</span>',
            canceled: '<span class="badge status-canceled">Скасовано</span>',
            free: '<span class="badge status-confirmed">Вільно</span>',
            booked: '<span class="badge status-pending">Зайнято</span>',
            paid: '<span class="badge status-confirmed">Оплачено</span>',
            unpaid: '<span class="badge status-pending">Не оплачено</span>',
            refunded: '<span class="badge status-canceled">Повернено</span>',
        };
        return map[status] || `<span class="badge">${esc(status || "—")}</span>`;
    };

    const actionButton = (label, action, entity, id, className) =>
        `<button type="button" class="${className}" data-action="${action}" data-entity="${entity}" data-id="${esc(id)}">${label}</button>`;

    const isPendingPayment = (payment) => !["paid", "refunded"].includes(String(payment?.status || ""));

    const getNameById = (items, id) => items.find((item) => String(item.id) === String(id))?.name || `#${id}`;

    const getBookingServiceOptions = (masterId, currentValue) => {
        const allowedServiceIds = masterId
            ? (state.users.find((user) => String(user.id) === String(masterId))?.services_offered || []).map(String)
            : state.services.map((service) => String(service.id));

        return state.services
            .filter((service) => allowedServiceIds.includes(String(service.id)))
            .map((service) => `<option value="${service.id}" ${String(currentValue) === String(service.id) ? "selected" : ""}>${esc(service.name)} (#${esc(service.id)})</option>`)
            .join("");
    };

    const getBookingTimeslotOptions = (masterId, currentValue) => {
        const slots = state.schedules.filter((slot) => {
            if (!masterId) return true;
            return String(slot.master_id) === String(masterId);
        });

        return slots
            .map((slot) => {
                const start = String(slot.start || "—").replace("T", " ").replace("Z", "");
                const end = String(slot.end || "—").replace("T", " ").replace("Z", "");
                const label = `#${slot.id} · ${start} - ${end} · ${slot.status || "—"}`;
                return `<option value="${slot.id}" ${String(currentValue) === String(slot.id) ? "selected" : ""}>${esc(label)}</option>`;
            })
            .join("");
    };

    const getUserFieldConfig = (record = {}, mode = "edit") => {
        if (mode === "create") {
            return ["name", "email", "password", "role"];
        }

        if (record.role === "admin") {
            return [];
        }

        if (record.role === "master") {
            return ["name", "email", "services_offered"];
        }

        return ["name", "email"];
    };

    const loadAll = async () => {
        const entities = ["bookings", "payments", "users", "services", "schedules", "feedback"];
        const results = await Promise.allSettled(entities.map((entity) => request(`/${entity}`)));

        const nextState = {};
        const failedEntities = [];

        entities.forEach((entity, index) => {
            const result = results[index];
            if (result.status === "fulfilled" && Array.isArray(result.value)) {
                nextState[entity] = result.value;
                return;
            }

            nextState[entity] = [];
            if (result.status === "rejected") {
                failedEntities.push(`${entity}: ${result.reason?.message || "помилка завантаження"}`);
            }
        });

        state = {
            bookings: nextState.bookings || [],
            payments: nextState.payments || [],
            users: nextState.users || [],
            services: nextState.services || [],
            schedules: nextState.schedules || [],
            feedback: nextState.feedback || [],
        };

        window.__adminState = state;
        renderAll();
        fillPaymentAcceptSelect();

        if (adminLoadStatus) {
            if (failedEntities.length) {
                adminLoadStatus.textContent = `Частина таблиць не завантажилась: ${failedEntities.join(" | ")}`;
                adminLoadStatus.hidden = false;
            } else {
                adminLoadStatus.textContent = "";
                adminLoadStatus.hidden = true;
            }
        }
    };

    const renderEmpty = (entity, message) => {
        const table = tables[entity];
        if (!table) return;

        const headers = {
            bookings: ["ID", "Клієнт", "Послуга", "Майстер", "Слот", "Статус", "Дії"],
            payments: ["ID", "Booking", "Сума", "Метод", "Статус", "Дії"],
            users: ["ID", "Ім'я", "Email", "Роль", "Дії"],
            services: ["ID", "Назва", "Ціна", "Час", "Дії"],
            schedules: ["ID", "Майстер", "Початок", "Статус", "Дії"],
            feedback: ["ID", "Клієнт", "Майстер", "Рейтинг", "Коментар", "Дії"],
        };

        table.innerHTML = `
            <thead><tr>${headers[entity].map((header) => `<th>${header}</th>`).join("")}</tr></thead>
            <tbody>
                <tr><td colspan="${headers[entity].length}" style="text-align:center; padding:16px;">${esc(message)}</td></tr>
            </tbody>
        `;
    };

    const renderTable = (entity, data) => {
        const table = tables[entity];
        if (!table) return;

        const headers = {
            bookings: ["ID", "Клієнт", "Послуга", "Майстер", "Слот", "Статус", "Дії"],
            payments: ["ID", "Booking", "Сума", "Метод", "Статус", "Дії"],
            users: ["ID", "Ім'я", "Email", "Роль", "Дії"],
            services: ["ID", "Назва", "Ціна", "Час", "Дії"],
            schedules: ["ID", "Майстер", "Початок", "Статус", "Дії"],
            feedback: ["ID", "Клієнт", "Майстер", "Рейтинг", "Коментар", "Дії"],
        };

        const rowHtml = (item) => {
            if (entity === "bookings") {
                return `
                    <tr>
                        <td>${esc(item.id)}</td>
                        <td>${esc(getNameById(state.users, item.client_id))}</td>
                        <td>${esc(getNameById(state.services, item.service_id))}</td>
                        <td>${esc(getNameById(state.users, item.master_id))}</td>
                        <td>${esc(item.timeslot_id || "—")}</td>
                        <td>${statusLabel(item.status)}</td>
                        <td class="admin-actions-cell">
                            ${actionButton("Редагувати", "edit", entity, item.id, "btn-row btn-row-edit")}
                            ${actionButton("Видалити", "delete", entity, item.id, "btn-row btn-row-delete")}
                        </td>
                    </tr>
                `;
            }

            if (entity === "payments") {
                return `
                    <tr>
                        <td>${esc(item.id)}</td>
                        <td>${esc(item.booking_id)}</td>
                        <td>${esc(item.amount)} грн</td>
                        <td>${esc(item.method || "—")}</td>
                        <td>${statusLabel(item.status)}</td>
                        <td class="admin-actions-cell">
                            ${actionButton("Редагувати", "edit", entity, item.id, "btn-row btn-row-edit")}
                            ${actionButton("Видалити", "delete", entity, item.id, "btn-row btn-row-delete")}
                        </td>
                    </tr>
                `;
            }

            if (entity === "users") {
                if (item.role === "admin") {
                    return `
                        <tr>
                            <td>${esc(item.id)}</td>
                            <td>${esc(item.name)}</td>
                            <td>${esc(item.email)}</td>
                            <td>${esc(item.role)}</td>
                            <td class="admin-actions-cell">
                                <span class="badge status-confirmed">Захищено</span>
                            </td>
                        </tr>
                    `;
                }

                return `
                    <tr>
                        <td>${esc(item.id)}</td>
                        <td>${esc(item.name)}</td>
                        <td>${esc(item.email)}</td>
                        <td>${esc(item.role)}</td>
                        <td class="admin-actions-cell">
                            ${actionButton("Редагувати", "edit", entity, item.id, "btn-row btn-row-edit")}
                            ${actionButton("Видалити", "delete", entity, item.id, "btn-row btn-row-delete")}
                        </td>
                    </tr>
                `;
            }

            if (entity === "services") {
                return `
                    <tr>
                        <td>${esc(item.id)}</td>
                        <td>${esc(item.name)}</td>
                        <td>${esc(item.price)} грн</td>
                        <td>${esc(item.duration_minutes)} хв</td>
                        <td class="admin-actions-cell">
                            ${actionButton("Редагувати", "edit", entity, item.id, "btn-row btn-row-edit")}
                            ${actionButton("Видалити", "delete", entity, item.id, "btn-row btn-row-delete")}
                        </td>
                    </tr>
                `;
            }

            if (entity === "schedules") {
                return `
                    <tr>
                        <td>${esc(item.id)}</td>
                        <td>${esc(getNameById(state.users, item.master_id))}</td>
                        <td>${esc(item.start || "—")}</td>
                        <td>${statusLabel(item.status)}</td>
                        <td class="admin-actions-cell">
                            ${actionButton("Редагувати", "edit", entity, item.id, "btn-row btn-row-edit")}
                            ${actionButton("Видалити", "delete", entity, item.id, "btn-row btn-row-delete")}
                        </td>
                    </tr>
                `;
            }

            return `
                <tr>
                    <td>${esc(item.id)}</td>
                    <td>${esc(getNameById(state.users, item.client_id))}</td>
                    <td>${esc(getNameById(state.users, item.master_id))}</td>
                    <td>${esc(item.rating)}★</td>
                    <td>${esc(item.comment || "—")}</td>
                    <td class="admin-actions-cell">
                        ${actionButton("Редагувати", "edit", entity, item.id, "btn-row btn-row-edit")}
                        ${actionButton("Видалити", "delete", entity, item.id, "btn-row btn-row-delete")}
                    </td>
                </tr>
            `;
        };

        table.innerHTML = `
            <thead><tr>${headers[entity].map((header) => `<th>${header}</th>`).join("")}</tr></thead>
            <tbody>
                ${data.length ? data.sort(idSort).map(rowHtml).join("") : `<tr><td colspan="${headers[entity].length}" style="text-align:center; padding:16px;">Немає даних</td></tr>`}
            </tbody>
        `;
    };

    const renderAll = () => {
        const safe = (entity) => {
            try {
                renderTable(entity, state[entity] || []);
            } catch (error) {
                console.error(`Failed to render ${entity}`, error);
                renderEmpty(entity, "Не вдалося відобразити дані");
            }
        };

        safe("bookings");
        safe("payments");
        safe("users");
        safe("services");
        safe("schedules");
        safe("feedback");
    };

    const getFieldConfig = (entity, record = {}, mode = "edit") => ({
        bookings: ["client_id", "master_id", "service_id", "timeslot_id", "status"],
        payments: ["booking_id", "amount", "method", "status"],
        users: getUserFieldConfig(record, mode),
        services: ["name", "price", "duration_minutes"],
        schedules: ["master_id", "start", "end", "status"],
        feedback: ["booking_id", "client_id", "master_id", "rating", "comment"],
    }[entity] || []);

    const selectOptions = (entity, field, currentValue, record = {}) => {
        if (entity === "bookings" && field === "client_id") {
            return state.users.filter((u) => u.role === "client")
                .map((u) => `<option value="${u.id}" ${String(currentValue) === String(u.id) ? "selected" : ""}>${esc(u.name)} (#${u.id})</option>`).join("");
        }
        if (entity === "bookings" && field === "master_id") {
            return state.users.filter((u) => u.role === "master")
                .map((u) => `<option value="${u.id}" ${String(currentValue) === String(u.id) ? "selected" : ""}>${esc(u.name)} (#${u.id})</option>`).join("");
        }
        if (entity === "bookings" && field === "service_id") {
            return getBookingServiceOptions(record.master_id, currentValue);
        }
        if (entity === "bookings" && field === "timeslot_id") {
            return getBookingTimeslotOptions(record.master_id, currentValue);
        }
        if (entity === "payments" && field === "booking_id") {
            return state.bookings
                .map((b) => `<option value="${b.id}" ${String(currentValue) === String(b.id) ? "selected" : ""}>Booking #${b.id}</option>`).join("");
        }
        if (entity === "users" && field === "role") {
            return ["client", "master"]
                .map((role) => `<option value="${role}" ${String(currentValue) === role ? "selected" : ""}>${role}</option>`).join("");
        }
        if (entity === "users" && field === "services_offered") {
            const selected = Array.isArray(currentValue) ? currentValue.map(String) : String(currentValue || "").split(",").map((item) => item.trim()).filter(Boolean);
            return state.services
                .map((s) => `<option value="${s.id}" ${selected.includes(String(s.id)) ? "selected" : ""}>${esc(s.name)}</option>`).join("");
        }
        if (entity === "schedules" && field === "master_id") {
            return state.users.filter((u) => u.role === "master")
                .map((u) => `<option value="${u.id}" ${String(currentValue) === String(u.id) ? "selected" : ""}>${esc(u.name)} (#${u.id})</option>`).join("");
        }
        if (entity === "schedules" && field === "status") {
            return ["free", "booked"].map((status) => `<option value="${status}" ${String(currentValue) === status ? "selected" : ""}>${status}</option>`).join("");
        }
        if (entity === "payments" && field === "status") {
            return ["unpaid", "paid", "refunded"].map((status) => `<option value="${status}" ${String(currentValue) === status ? "selected" : ""}>${status}</option>`).join("");
        }
        if (entity === "payments" && field === "method") {
            return ["card", "cash"].map((method) => `<option value="${method}" ${String(currentValue) === method ? "selected" : ""}>${method}</option>`).join("");
        }
        if (entity === "bookings" && field === "status") {
            return [
                { value: "completed", label: "Виконано" },
                { value: "pending", label: "Не виконано" },
            ].map(({ value, label }) => `<option value="${value}" ${String(currentValue) === value ? "selected" : ""}>${label}</option>`).join("");
        }
        if (entity === "feedback" && field === "booking_id") {
            return state.bookings
                .map((b) => `<option value="${b.id}" ${String(currentValue) === String(b.id) ? "selected" : ""}>Booking #${b.id}</option>`).join("");
        }
        if (entity === "feedback" && field === "client_id") {
            return state.users.filter((u) => u.role === "client")
                .map((u) => `<option value="${u.id}" ${String(currentValue) === String(u.id) ? "selected" : ""}>${esc(u.name)} (#${u.id})</option>`).join("");
        }
        if (entity === "feedback" && field === "master_id") {
            return state.users.filter((u) => u.role === "master")
                .map((u) => `<option value="${u.id}" ${String(currentValue) === String(u.id) ? "selected" : ""}>${esc(u.name)} (#${u.id})</option>`).join("");
        }
        return "";
    };

    const generateFields = async (entity, record = {}, mode = "edit") => {
        const container = document.getElementById("formFields");
        container.innerHTML = "";
        const fields = getFieldConfig(entity, record, mode);

        for (const field of fields) {
            const value = Array.isArray(record[field]) ? record[field] : (record[field] ?? "");
            const label = `<label style="display:block; margin-top:10px; font-size:10px; text-transform:uppercase; letter-spacing:0.14em;">${field}</label>`;

            if (["client_id", "master_id", "service_id", "booking_id", "role", "method", "status"].includes(field)) {
                const options = selectOptions(entity, field, value, record);
                container.innerHTML += `
                    ${label}
                    <select name="${field}" style="width:100%; padding:10px; margin-top:6px; border:1px solid #ddd; border-radius:12px;" ${["booking_id", "client_id", "master_id", "service_id"].includes(field) ? "required" : ""}>
                        <option value="">-- Оберіть --</option>
                        ${options}
                    </select>
                `;
                continue;
            }

            if (entity === "users" && field === "services_offered") {
                const selected = Array.isArray(value) ? value : String(value || "").split(",").map((item) => item.trim()).filter(Boolean);
                container.innerHTML += `
                    ${label}
                    <select name="${field}" multiple size="4" style="width:100%; padding:10px; margin-top:6px; border:1px solid #ddd; border-radius:12px;">
                        ${selectOptions(entity, field, selected, record)}
                    </select>
                `;
                continue;
            }

            let type = "text";
            if (field === "password") type = "password";
            if (["price", "amount", "rating", "duration_minutes"].includes(field)) type = "number";
            if (["start", "end", "paid_at"].includes(field)) type = "datetime-local";

            const inputValue = ["start", "end", "paid_at"].includes(field) && value ? String(value).slice(0, 16) : value;
            const extraAttrs = entity === "feedback" && field === "rating" ? ' min="1" max="5" step="1"' : "";
            container.innerHTML += `${label}<input name="${field}" type="${type}"${extraAttrs} value="${esc(inputValue)}" style="width:100%; padding:10px; margin-top:6px; border:1px solid #ddd; border-radius:12px;">`;
        }

        if (entity === "bookings") {
            const masterSelect = container.querySelector('select[name="master_id"]');
            const serviceSelect = container.querySelector('select[name="service_id"]');
            const timeslotSelect = container.querySelector('select[name="timeslot_id"]');

            const syncBookingDependencies = () => {
                const masterId = masterSelect?.value || "";
                if (serviceSelect) {
                    const selectedService = serviceSelect.value;
                    serviceSelect.innerHTML = '<option value="">-- Оберіть --</option>' + getBookingServiceOptions(masterId, selectedService);
                    if (!Array.from(serviceSelect.options).some((option) => option.value === selectedService)) {
                        serviceSelect.value = serviceSelect.options[1]?.value || "";
                    }
                }

                if (timeslotSelect) {
                    const selectedTimeslot = timeslotSelect.value;
                    timeslotSelect.innerHTML = '<option value="">-- Оберіть --</option>' + getBookingTimeslotOptions(masterId, selectedTimeslot);
                    if (!Array.from(timeslotSelect.options).some((option) => option.value === selectedTimeslot)) {
                        timeslotSelect.value = timeslotSelect.options[1]?.value || "";
                    }
                }
            };

            masterSelect?.addEventListener("change", syncBookingDependencies);
            syncBookingDependencies();
        }
    };

    const parsePayload = (entity, formData) => {
        const payload = Object.fromEntries(formData.entries());
        const numericFields = ["price", "amount", "rating", "duration_minutes"];
        numericFields.forEach((field) => {
            if (payload[field] !== undefined && payload[field] !== "") {
                payload[field] = Number(payload[field]);
            }
        });

        if (entity === "feedback" && payload.rating !== undefined && payload.rating !== "") {
            payload.rating = Math.max(1, Math.min(5, Math.round(Number(payload.rating))));
        }

        if (entity === "users" && payload.services_offered !== undefined) {
            const selected = formData.getAll("services_offered");
            payload.services_offered = selected.length ? selected : [];
        }

        if (entity === "bookings" && payload.status) {
            payload.status = payload.status === "completed" ? "completed" : "pending";
        }

        return payload;
    };

    const fillPaymentAcceptSelect = () => {
        if (!paymentAcceptSelect) return;

        const pendingPayments = state.payments.filter(isPendingPayment);
        paymentAcceptSelect.innerHTML = '<option value="">Оберіть платіж</option>' + pendingPayments
            .map((payment) => `<option value="${payment.id}">#${payment.id} · Booking #${payment.booking_id} · ${payment.amount} грн · ${payment.method || "—"} · ${payment.status || "—"}</option>`)
            .join("");
    };

    window.openAddModal = async (entity) => {
        window.__currentEntity = entity;
        window.__currentId = null;
        window.__currentRecord = null;
        window.__currentMode = "create";
        document.getElementById("modalTitle").textContent = `ДОДАТИ ${entity.toUpperCase()}`;
        await generateFields(entity, {}, "create");
        document.getElementById("adminModal").style.display = "block";
    };

    window.openEditModal = async (entity, id) => {
        const source = state[entity] || [];
        const record = source.find((item) => String(item.id) === String(id));

        if (!record) {
            alert("Запис не знайдено.");
            return;
        }

        if (entity === "users" && record.role === "admin") {
            alert("Адміністратора редагувати не можна.");
            return;
        }

        window.__currentEntity = entity;
        window.__currentId = id;
        window.__currentRecord = record;
        window.__currentMode = "edit";
        document.getElementById("modalTitle").textContent = `РЕДАГУВАТИ ${entity.toUpperCase()}`;
        await generateFields(entity, record, "edit");
        document.getElementById("adminModal").style.display = "block";
    };

    window.closeModal = () => {
        document.getElementById("adminModal").style.display = "none";
    };

    document.getElementById("adminForm").addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        const entity = window.__currentEntity;
        const currentId = window.__currentId;
        const payload = parsePayload(entity, formData);

        if (entity === "users" && !currentId && !["client", "master"].includes(payload.role)) {
            alert("Адміну не можна створювати через форму.");
            return;
        }

        try {
            const method = currentId ? "PATCH" : "POST";
            const url = currentId ? `/${entity}/${currentId}` : `/${entity}`;
            await request(url, method, payload);
            alert("Успішно збережено!");
            window.closeModal();
            await loadAll();
        } catch (error) {
            alert(error.message || "Не вдалося зберегти запис.");
        }
    });

    window.deleteRecord = async (entity, id) => {
        if (!confirm("Видалити запис?")) return;

        try {
            await request(`/${entity}/${id}`, "DELETE");
            await loadAll();
        } catch (error) {
            alert(error.message || "Не вдалося видалити запис.");
        }
    };

    window.acceptPayment = async (paymentId) => {
        try {
            await request(`/payments/${paymentId}/accept`, "PATCH");
            await loadAll();
        } catch (error) {
            alert(error.message || "Не вдалося прийняти оплату.");
        }
    };

    acceptSelectedPaymentBtn?.addEventListener("click", async () => {
        const paymentId = paymentAcceptSelect?.value;
        if (!paymentId) {
            alert("Оберіть платіж.");
            return;
        }
        await window.acceptPayment(paymentId);
    });

    document.addEventListener("click", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;

        const action = target.dataset.action;
        const entity = target.dataset.entity;
        const id = target.dataset.id;

        if (action === "edit" && entity && id) {
            window.openEditModal(entity, id);
        }

        if (action === "delete" && entity && id) {
            window.deleteRecord(entity, id);
        }

        if (action === "accept-payment" && id) {
            window.acceptPayment(id);
        }
    });

    await loadAll();
});
