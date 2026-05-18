document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("access_token");
    const userStr = localStorage.getItem("user");
    const bookingSelect = document.getElementById("bookingSelect");
    const bookingInfo = document.getElementById("bookingInfo");
    const form = document.getElementById("feedbackForm");

    if (!token || !userStr) {
        window.location.href = "login.html";
        return;
    }

    const user = JSON.parse(userStr);
    const queryBookingId = new URLSearchParams(window.location.search).get("booking_id");
    const FEEDBACK_DELAY_MS = 24 * 60 * 60 * 1000;

    const [bookings, services, masters, feedbacks] = await Promise.all([
        request(`/bookings/user/${user.id}?include_deleted=true`),
        request("/services"),
        request("/users/masters"),
        request(`/feedback?client_id=${user.id}`),
    ]);

    const servicesMap = new Map((services || []).map((service) => [String(service.id), service.name]));
    const mastersMap = new Map((masters || []).map((master) => [String(master.id), master.name]));
    const feedbackBookedIds = new Set((feedbacks || []).map((item) => String(item.booking_id)));

    const paymentMap = new Map();
    await Promise.all((bookings || []).map(async (booking) => {
        try {
            const payments = await request(`/payments/booking/${booking.id}`);
            paymentMap.set(String(booking.id), Array.isArray(payments) && payments.some((payment) => payment.status === "paid"));
        } catch (error) {
            paymentMap.set(String(booking.id), false);
        }
    }));

    const eligible = (bookings || []).filter((booking) => (
        String(booking.status || "").toLowerCase() === "completed"
        && paymentMap.get(String(booking.id))
        && (new Date(booking.updated_at || booking.created_at || 0).getTime() + FEEDBACK_DELAY_MS) <= Date.now()
        && !feedbackBookedIds.has(String(booking.id))
    ));

    const bookingReadyAt = (booking) => new Date(booking.updated_at || booking.created_at || 0).getTime() + FEEDBACK_DELAY_MS;
    const formatCountdown = (milliseconds) => {
        const totalSeconds = Math.max(0, Math.ceil(milliseconds / 1000));
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    };

    if (!eligible.length) {
        const waiting = (bookings || [])
            .filter((booking) => String(booking.status || "").toLowerCase() === "completed" && paymentMap.get(String(booking.id)) && !feedbackBookedIds.has(String(booking.id)))
            .sort((a, b) => bookingReadyAt(a) - bookingReadyAt(b))[0];

        bookingSelect.innerHTML = '<option value="">Немає доступних записів для відгуку</option>';
        form.querySelector('button[type="submit"]').disabled = true;

        if (bookingInfo) {
            bookingInfo.hidden = false;
            const waitingCountdown = waiting ? Math.max(0, bookingReadyAt(waiting) - Date.now()) : 0;
            const waitingCountdownHtml = waitingCountdown > 0 ? `<div>До доступу: ${formatCountdown(waitingCountdown)}</div>` : "";
            bookingInfo.innerHTML = `
                <div class="feedback-info">
                    <strong>Відгук ще недоступний</strong>
                    <div>Майбутній запис з'явиться після завершення добового відліку.</div>
                    ${waiting ? `<div>Майстер: ${mastersMap.get(String(waiting.master_id)) || "Майстер"}</div><div>Послуга: ${servicesMap.get(String(waiting.service_id)) || "Послуга"}</div>${waitingCountdownHtml}` : ""}
                </div>
            `;
        }
        return;
    }

    bookingSelect.innerHTML = '<option value="">-- Оберіть запис --</option>' + eligible.map((booking) => {
        const serviceName = servicesMap.get(String(booking.service_id)) || "Послуга";
        const masterName = mastersMap.get(String(booking.master_id)) || "Майстер";
        const readyIn = Math.max(0, bookingReadyAt(booking) - Date.now());
        const countdownText = readyIn > 0 ? ` · ${formatCountdown(readyIn)}` : "";
        return `<option value="${booking.id}" data-master="${booking.master_id}" data-service="${booking.service_id}" data-date="${booking.updated_at || booking.created_at || ""}" data-ready-at="${bookingReadyAt(booking)}">${serviceName} · ${masterName}${countdownText}</option>`;
    }).join("");

    const renderSelectedBooking = (option) => {
        if (!option || !option.value) {
            bookingInfo.hidden = true;
            return;
        }

        const readyAt = Number(option.dataset.readyAt || 0);
        const remaining = readyAt - Date.now();
        const serviceName = servicesMap.get(String(option.dataset.service)) || "Послуга";
        const masterName = mastersMap.get(String(option.dataset.master)) || "Майстер";
        const dateText = option.dataset.date ? new Date(option.dataset.date).toLocaleString("uk-UA") : "Невідомо";

        const remainingSafe = Math.max(0, remaining);
        const remainingHtml = remainingSafe > 0 ? `<div>До відкриття відгуку: ${formatCountdown(remainingSafe)}</div>` : "";
        bookingInfo.innerHTML = `
            <div class="feedback-info">
                <strong>Запис готовий для відгуку</strong>
                <div>Майстер: ${masterName}</div>
                <div>Послуга: ${serviceName}</div>
                <div>Дата завершення: ${dateText}</div>
                ${remainingHtml}
                <div>Оцінка від 1 до 5 зірок та короткий коментар допоможуть майстру покращувати сервіс.</div>
            </div>
        `;
        bookingInfo.hidden = false;
    };

    if (queryBookingId) {
        bookingSelect.value = queryBookingId;
    }
    renderSelectedBooking(bookingSelect.selectedOptions[0]);

    bookingSelect.addEventListener("change", (event) => {
        renderSelectedBooking(event.target.selectedOptions[0]);
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const option = bookingSelect.selectedOptions[0];
        if (!option || !option.value) {
            alert("Оберіть запис для відгуку.");
            return;
        }

        try {
            await request("/feedback", "POST", {
                booking_id: String(option.value),
                client_id: String(user.id),
                master_id: String(option.dataset.master),
                rating: Number(document.getElementById("rating").value),
                comment: document.getElementById("comment").value.trim(),
            });
            alert("Дякуємо за ваш відгук!");
            window.location.href = "../index.html";
        } catch (error) {
            alert(error.message || "Не вдалося надіслати відгук.");
        }
    });
});
