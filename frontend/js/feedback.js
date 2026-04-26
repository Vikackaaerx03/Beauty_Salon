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

    const [bookings, services, users, feedbacks] = await Promise.all([
        request(`/bookings/user/${user.id}`),
        request("/services"),
        request("/users/masters"),
        request(`/feedback?client_id=${user.id}`),
    ]);

    const servicesMap = new Map((services || []).map((service) => [String(service.id), service.name]));
    const usersMap = new Map((users || []).map((master) => [String(master.id), master.name]));
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
        booking.status === "completed"
        && paymentMap.get(String(booking.id))
        && !feedbackBookedIds.has(String(booking.id))
    ));

    if (!eligible.length) {
        bookingSelect.innerHTML = '<option value="">Немає доступних записів для відгуку</option>';
        form.querySelector('button[type="submit"]').disabled = true;
        return;
    }

    bookingSelect.innerHTML = '<option value="">-- Оберіть запис --</option>' + eligible.map((booking) => {
        const serviceName = servicesMap.get(String(booking.service_id)) || "Послуга";
        const masterName = usersMap.get(String(booking.master_id)) || "Майстер";
        return `<option value="${booking.id}" data-master="${booking.master_id}" data-service="${booking.service_id}" data-date="${booking.updated_at || booking.created_at || ""}">${serviceName} - ${masterName}</option>`;
    }).join("");

    if (queryBookingId) {
        bookingSelect.value = queryBookingId;
        bookingSelect.dispatchEvent(new Event("change"));
    }

    bookingSelect.addEventListener("change", (event) => {
        const option = event.target.selectedOptions[0];
        if (!option || !option.value) {
            bookingInfo.hidden = true;
            return;
        }

        document.getElementById("serviceName").textContent = servicesMap.get(String(option.dataset.service)) || "Послуга";
        document.getElementById("masterName").textContent = usersMap.get(String(option.dataset.master)) || "Майстер";
        document.getElementById("bookingDate").textContent = option.dataset.date ? new Date(option.dataset.date).toLocaleString("uk-UA") : "Невідомо";
        document.getElementById("paymentStatus").innerHTML = '<span class="status-confirmed">Оплачено</span>';
        bookingInfo.hidden = false;
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
