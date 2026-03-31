document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem('access_token');
    const userRole = localStorage.getItem('role');

    if (!token || userRole !== 'admin') {
        alert("Доступ заборонено. Тільки для адміністраторів.");
        window.location.href = '../index.html';
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

    let currentEntity = '';
    let currentId = null;

    async function loadAdminData() {
        const entities = ['bookings', 'payments', 'users', 'services', 'schedules', 'feedback'];
        for (const entity of entities) {
            try {
                let data = await request(`/${entity}`, "GET");
                if (!data) data = [];

                if (entity === 'schedules') {
                    data.sort((a, b) => new Date(a.start) - new Date(b.start));
                } else {
                    data.sort((a, b) => parseInt(a.id) - parseInt(b.id));
                }
                renderEntityTable(entity, data);
            } catch (error) {
                console.warn(`Помилка завантаження ${entity}:`, error);
                if (tables[entity]) {
                    tables[entity].innerHTML = `<tr><td style="color:orange; padding:10px;">Помилка доступу</td></tr>`;
                }
            }
        }
    }

    function renderEntityTable(entity, data) {
        const table = tables[entity];
        if (!table) return;

        let header = '';
        if (entity === 'bookings') header = `<thead><tr><th>ID</th><th>Клієнт</th><th>Послуга</th><th>Майстер</th><th>Слот</th><th>Дії</th></tr></thead>`;
        else if (entity === 'payments') header = `<thead><tr><th>ID</th><th>Booking</th><th>Сума</th><th>Метод</th><th>Дії</th></tr></thead>`;
        else if (entity === 'users') header = `<thead><tr><th>ID</th><th>Ім'я</th><th>Email</th><th>Роль</th><th>Дії</th></tr></thead>`;
        else if (entity === 'services') header = `<thead><tr><th>ID</th><th>Назва</th><th>Ціна</th><th>Час</th><th>Дії</th></tr></thead>`;
        else if (entity === 'schedules') header = `<thead><tr><th>ID</th><th>Майстер</th><th>Початок</th><th>Статус</th><th>Дії</th></tr></thead>`;
        else if (entity === 'feedback') header = `<thead><tr><th>ID</th><th>Master</th><th>⭐</th><th>Дії</th></tr></thead>`;

        const rows = data.map(item => {
            const dataStr = encodeURIComponent(JSON.stringify(item));
            let cells = '';

            if (entity === 'bookings') {
                cells = `<td>${item.id}</td><td>${item.client_id}</td><td>${item.service_id}</td><td>${item.master_id}</td><td>${item.timeslot_id}</td>`;
            } else if (entity === 'payments') {
                cells = `<td>${item.id}</td><td>${item.booking_id}</td><td>${item.amount} грн</td><td>${item.method}</td>`;
            } else if (entity === 'users') {
                cells = `<td>${item.id}</td><td><b>${item.name}</b></td><td>${item.email}</td><td>${item.role}</td>`;
            } else if (entity === 'services') {
                cells = `<td>${item.id}</td><td>${item.name}</td><td>${item.price}</td><td>${item.duration_minutes} хв</td>`;
            } else if (entity === 'schedules') {
                const time = item.start ? new Date(item.start).toLocaleString('uk-UA', {hour:'2-digit', minute:'2-digit', day:'2-digit', month:'2-digit'}) : '-';
                cells = `<td>${item.id}</td><td>${item.master_id}</td><td>${time}</td><td>${item.status}</td>`;
            } else if (entity === 'feedback') {
                cells = `<td>${item.id}</td><td>${item.master_id}</td><td>${item.rating}⭐</td>`;
            }

            return `<tr>${cells}<td>
                <button class="btn-edit" onclick="openEditModal('${entity}', '${item.id}', '${dataStr}')">✎</button>
                <button class="btn-delete" onclick="window.deleteRecord('${entity}', '${item.id}')">🗑</button>
            </td></tr>`;
        }).join("");

        table.innerHTML = `${header}<tbody>${data.length ? rows : '<tr><td colspan="6" style="text-align:center; padding:15px; opacity:0.5;">Немає даних</td></tr>'}</tbody>`;
    }

    window.openAddModal = (entity) => {
        currentEntity = entity;
        currentId = null;
        document.getElementById('modalTitle').innerText = `ДОДАТИ В ${entity.toUpperCase()}`;
        generateFields(entity);
        document.getElementById('adminModal').style.display = 'block';
    };

    window.openEditModal = (entity, id, encoded) => {
        currentEntity = entity;
        currentId = id;
        document.getElementById('modalTitle').innerText = `РЕДАГУВАТИ ${entity.toUpperCase()}`;
        generateFields(entity, JSON.parse(decodeURIComponent(encoded)));
        document.getElementById('adminModal').style.display = 'block';
    };

    window.closeModal = () => document.getElementById('adminModal').style.display = 'none';

    function generateFields(entity, data = {}) {
        const container = document.getElementById('formFields');
        container.innerHTML = '';
        const config = {
            bookings: ['client_id', 'master_id', 'service_id', 'timeslot_id', 'status'],
            services: ['name', 'price', 'duration_minutes', 'description'],
            users: ['name', 'email', 'role', 'password'],
            payments: ['booking_id', 'amount', 'method', 'status'],
            schedules: ['master_id', 'start', 'end', 'status'],
            feedback: ['booking_id', 'master_id', 'client_id', 'rating', 'comment']
        };

        config[entity].forEach(f => {
            const val = data[f] || '';
            let type = (f === 'password') ? 'password' : 'text';
            if (f === 'start' || f === 'end') type = 'datetime-local';
            if (['price', 'amount', 'rating', 'duration_minutes', 'master_id', 'client_id', 'service_id', 'timeslot_id', 'booking_id'].includes(f)) type = 'number';

            container.innerHTML += `<label style="font-size:10px; display:block; margin-top:10px; color:#666; text-transform:uppercase;">${f}</label>
                <input type="${type}" name="${f}" value="${val}" required style="width:100%; box-sizing:border-box; padding:10px; border:1px solid #ddd; border-radius:2px;">`;
        });
    }

    document.getElementById('adminForm').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const rawData = Object.fromEntries(formData.entries());
        const payload = { ...rawData };

        const numericFields = ['client_id', 'master_id', 'service_id', 'timeslot_id', 'booking_id', 'amount', 'price', 'rating', 'duration_minutes'];
        numericFields.forEach(field => {
            if (payload[field]) payload[field] = parseInt(payload[field]);
        });

        if (payload.start) payload.start = new Date(payload.start).toISOString();
        if (payload.end) payload.end = new Date(payload.end).toISOString();

        try {
            const method = currentId ? "PATCH" : "POST";
            const url = currentId ? `/${currentEntity}/${currentId}` : `/${currentEntity}`;
            await request(url, method, payload);
            alert("Успішно збережено!");
            closeModal();
            loadAdminData();
        } catch (err) {
            try {
                const stringPayload = { ...rawData };
                const method = currentId ? "PATCH" : "POST";
                const url = currentId ? `/${currentEntity}/${currentId}` : `/${currentEntity}`;
                await request(url, method, stringPayload);
                alert("Збережено успішно!");
                closeModal();
                loadAdminData();
            } catch (finalErr) {
                let msg = finalErr.detail;
                if (Array.isArray(msg)) msg = msg.map(d => `${d.loc.at(-1)}: ${d.msg}`).join('\n');
                alert("Помилка валідації:\n" + (msg || finalErr.message));
            }
        }
    };

    window.deleteRecord = async (entity, id) => {
        if (!confirm("Видалити цей запис?")) return;
        try {
            await request(`/${entity}/${id}`, "DELETE");
            loadAdminData();
        } catch (err) { alert("Помилка видалення: " + err.message); }
    };

    loadAdminData();
});