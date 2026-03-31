document.addEventListener("DOMContentLoaded", async () => {
    const userStr = localStorage.getItem("user");
    const token = localStorage.getItem("access_token");

    // 1. ПЕРЕВІРКА АВТОРИЗАЦІЇ
    if (!token || !userStr) {
        window.location.href = "login.html";
        return;
    }

    let user = JSON.parse(userStr);
    const nameInput = document.getElementById("editName");
    const emailInput = document.getElementById("editEmail");
    const bookingsList = document.getElementById("userBookingsList");

    // Заповнюємо інпути даними з пам'яті
    if (nameInput) nameInput.value = user.name || "";
    if (emailInput) emailInput.value = user.email || "";

    // 2. РОЗУМНЕ ОНОВЛЕННЯ ПРОФІЛЮ
    const profileForm = document.getElementById("editProfileForm");
    if (profileForm) {
        profileForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const newName = nameInput.value.trim();
            const newEmail = emailInput.value.trim();

            // Перевірка: чи змінилося бодай щось?
            if (newName === user.name && newEmail === user.email) {
                alert("Ви не внесли жодних змін.");
                return;
            }

            // КЛЮЧОВИЙ МОМЕНТ: Формуємо об'єкт ТІЛЬКИ зі зміненими полями
            // Це обходить помилку "Email вже зайнятий", якщо ти його не міняла
            const updatedFields = {};
            if (newName !== user.name) {
                updatedFields.name = newName;
            }
            if (newEmail !== user.email) {
                updatedFields.email = newEmail;
            }

            try {
                // Використовуємо PATCH для часткового оновлення
                const result = await request(`/users/${user.id}`, "PATCH", updatedFields);
                
                if (result) {
                    // Оновлюємо об'єкт користувача в пам'яті (merge старих і нових даних)
                    const updatedUser = { ...user, ...updatedFields };
                    localStorage.setItem("user", JSON.stringify(updatedUser));
                    
                    alert("Профіль успішно оновлено!");
                    window.location.reload(); 
                }
            } catch (err) {
                console.error("Update error:", err);
                
                // Якщо PATCH не підтримується, пробуємо PUT, але теж тільки зі змінами
                try {
                    const resultPut = await request(`/users/${user.id}`, "PUT", updatedFields);
                    if (resultPut) {
                        const updatedUser = { ...user, ...updatedFields };
                        localStorage.setItem("user", JSON.stringify(updatedUser));
                        alert("Дані оновлено!");
                        window.location.reload();
                    }
                } catch (putErr) {
                    // Якщо і тут помилка — значить такий імейл реально вже у КОГОСЬ ІНШОГО
                    alert("Помилка: Можливо, цей Email вже використовується іншим користувачем.");
                }
            }
        });
    }

    // 3. ЗАВАНТАЖЕННЯ ІСТОРІЇ (з виправленням можливих помилок шляху)
    async function loadUserHistory() {
        if (!bookingsList) return;
        
        try {
            const bookings = await request(`/bookings/user/${user.id}`, "GET");
            
            bookingsList.innerHTML = ""; 

            if (!bookings || bookings.length === 0) {
                bookingsList.innerHTML = "<p class='no-data'>У вас ще немає записів.</p>";
                return;
            }

            bookings.forEach(b => {
                const statusClass = b.status === 'confirmed' ? 'status-confirmed' : 'status-pending';
                bookingsList.innerHTML += `
                    <div class="booking-history-item">
                        <div class="booking-header">
                            <span class="service-name">${b.service_name || 'Послуга'}</span>
                            <span class="badge ${statusClass}">${b.status || 'pending'}</span>
                        </div>
                        <div class="booking-details">
                            <span>Дата: ${b.date}</span> | <span>Час: ${b.time}</span>
                        </div>
                        <div class="master-info">Майстер: ${b.master_name || 'Не вказано'}</div>
                    </div>`;
            });
        } catch (e) {
            console.error("History loading error:", e);
            bookingsList.innerHTML = "<p class='error-text'>Історія записів зараз недоступна.</p>";
        }
    }

    await loadUserHistory();
});