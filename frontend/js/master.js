document.addEventListener("DOMContentLoaded", async () => {

    const scheduleContainer = document.getElementById("scheduleContainer");
    const mastersGrid = document.getElementById("mastersGrid");
    const sortSelect = document.getElementById("sortMasters");

    if (mastersGrid) {

        const loadPublicMasters = async () => {
            const sortVal = sortSelect ? sortSelect.value : "name";

            try {
                const masters = await request(`/users/masters?sort=${sortVal}`);
                mastersGrid.innerHTML = "";

                if (!masters || masters.length === 0) {
                    mastersGrid.innerHTML = "<p>Майстрів не знайдено.</p>";
                    return;
                }

                masters.forEach((m) => {
                    let avatarFile = "default.jpg"; 
                    if (m.name === "Олена Гринчук") avatarFile = "icon_1.jpg";
                    if (m.name === "Ольга Вірник")  avatarFile = "icon_2.jpg";
                    if (m.name === "Таня Мірошник") avatarFile = "icon_3.jpg";
                    if (m.name === "Аліна Колос")   avatarFile = "icon_4.jpg";

                    const avatarPath = `../assets/images/${avatarFile}`;

                    const rating = m.rating || 0;
                    const fullStars = '★'.repeat(Math.floor(rating));
                    const emptyStars = '☆'.repeat(5 - Math.floor(rating));

                    const card = document.createElement("div");
                    card.className = "master-card";

                    card.innerHTML = `
                        <div class="master-avatar-wrapper">
                            <img src="${avatarPath}" 
                                 alt="${m.name}" 
                                 class="master-avatar">
                        </div>

                        <h3 class="master-name">${m.name}</h3>

                        <div class="master-rating">
                            <span class="stars">${fullStars}${emptyStars}</span>
                            <span class="rating-value">${rating}</span>
                        </div>
                    `;
                    const img = card.querySelector("img");
                    img.onerror = () => {
                        img.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(m.name)}&background=random&color=fff&size=128`;
                    };

                    mastersGrid.appendChild(card);
                });

            } catch (e) {
                console.error("Помилка завантаження майстрів:", e);
                mastersGrid.innerHTML = "<p>Помилка завантаження даних.</p>";
            }
        };

        loadPublicMasters();

        if (sortSelect) {
            sortSelect.addEventListener("change", loadPublicMasters);
        }
    }


    if (scheduleContainer) {
        try {
            const mySchedule = await request("/schedules/my");
            scheduleContainer.innerHTML = (mySchedule && mySchedule.length) ? "" : "<p>Наразі записів немає.</p>";

            if (mySchedule) {
                mySchedule.forEach(s => {
                    scheduleContainer.innerHTML += `
                        <div class="schedule-item">
                            <div class="schedule-info">
                                <h4>${s.date} о ${s.time}</h4>
                                <p>Клієнт: <strong>${s.client_name}</strong> | Послуга: ${s.service_name}</p>
                            </div>
                            <button onclick="markAsDone('${s.id}')" class="btn-premium">ВИКОНАНО</button>
                        </div>
                    `;
                });
            }
        } catch (e) {
            console.error("Помилка розкладу:", e);
        }
    }
});

window.markAsDone = async function (id) {
    if (!confirm("Позначити цей запис як виконаний?")) return;
    try {
        await request(`/bookings/${id}/complete`, "PUT");
        location.reload();
    } catch (e) {
        console.error("Помилка завершення запису:", e);
    }
};