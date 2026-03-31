document.addEventListener("DOMContentLoaded", async () => {
    const serviceSelect = document.getElementById("serviceSelect");
    const masterSelect = document.getElementById("masterSelect");
    const timeslotSelect = document.getElementById("timeslotSelect");
    const bookingForm = document.getElementById("bookingForm");

    try {
        const services = await request("/services"); 
        if (serviceSelect) {
            serviceSelect.innerHTML = '<option value="">-- Оберіть послугу --</option>';
            services.forEach(s => {
                serviceSelect.innerHTML += `<option value="${s.id}">${s.name} (${s.price} грн)</option>`;
            });
        }
    } catch (e) {
        console.error("Помилка завантаження послуг", e);
    }

    try {
        const masters = await request("/users/masters"); 
        if (masterSelect) {
            masterSelect.innerHTML = '<option value="">-- Оберіть майстра --</option>';
            masters.forEach(m => {
                masterSelect.innerHTML += `<option value="${m.id}">${m.name} (⭐ ${m.rating || 0})</option>`;
            });
        }
    } catch (e) {
        console.error("Помилка завантаження майстрів", e);
    }

    if (masterSelect && timeslotSelect) {
        masterSelect.addEventListener("change", async (e) => {
            const masterId = e.target.value;
            if (!masterId) return;

            timeslotSelect.innerHTML = '<option value="">Шукаємо вільний час...</option>';

            try {
                const slots = await request(`/schedules?master_id=${masterId}&status_filter=free`);
                
                if (!slots || slots.length === 0) {
                    timeslotSelect.innerHTML = '<option value="">Немає вільних місць</option>';
                } else {
                    timeslotSelect.innerHTML = '<option value="">-- Оберіть зручний час --</option>';
                    slots.forEach(slot => {
                        const dateObj = new Date(slot.start);
                        const formatted = dateObj.toLocaleString('uk-UA', { 
                            day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' 
                        });
                        timeslotSelect.innerHTML += `<option value="${slot.id}">${formatted}</option>`;
                    });
                }
            } catch (err) {
                timeslotSelect.innerHTML = '<option value="">Помилка завантаження слотів</option>';
            }
        });
    }

    if (bookingForm) {
        bookingForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const sId = serviceSelect.value;
            const mId = masterSelect.value;
            const tId = timeslotSelect.value;

            if (!sId || !mId || !tId) {
                alert("Будь ласка, оберіть послугу, майстра та час!");
                return;
            }

            const data = {
                service_id: sId.toString(),
                master_id: mId.toString(),
                timeslot_id: tId.toString() 
            };

            console.log("Відправляємо дані (як рядки):", data);

            try {
                const res = await request("/bookings", "POST", data);
                if (res) {
                    alert("Чудово! Ви успішно записані.");
                    window.location.href = "profile.html"; 
                }
            } catch (error) {
                console.error("DEBUG:", error);
                
                if (error.detail && Array.isArray(error.detail)) {
                    const msg = error.detail.map(d => {
                        const field = d.loc[d.loc.length - 1];
                        return `Поле [${field}]: ${d.msg}`;
                    }).join("\n");
                    alert("СЕРВЕР ВСЕ ОДНО НЕ ПРИЙНЯВ ДАНІ:\n" + msg);
                } else {
                    alert("Помилка: " + error.message);
                }
            }
        });
    }
});