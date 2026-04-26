document.addEventListener("DOMContentLoaded", async () => {
    const userStr = localStorage.getItem("user");
    const token = localStorage.getItem("access_token");

    if (!token || !userStr) {
        window.location.href = "login.html";
        return;
    }

    let user = null;
    try {
        user = JSON.parse(userStr);
    } catch (error) {
        window.location.href = "login.html";
        return;
    }

    const nameInput = document.getElementById("editName");
    const emailInput = document.getElementById("editEmail");
    const bookingsList = document.getElementById("userBookingsList");
    const mailNotifications = document.getElementById("mailNotifications");
    const profileAvatarPreview = document.getElementById("profileAvatarPreview");
    const profileAvatarFile = document.getElementById("profileAvatarFile");

    if (nameInput) nameInput.value = user.name || "";
    if (emailInput) emailInput.value = user.email || "";

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
            <svg xmlns="http://www.w3.org/2000/svg" width="240" height="240" viewBox="0 0 240 240">
                <defs>
                    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="${colors[0]}"/>
                        <stop offset="100%" stop-color="${colors[1]}"/>
                    </linearGradient>
                </defs>
                <rect width="240" height="240" rx="40" fill="url(#g)"/>
                <circle cx="120" cy="92" r="48" fill="rgba(255,255,255,0.18)"/>
                <text x="120" y="140" text-anchor="middle" font-family="Montserrat, Arial, sans-serif" font-size="64" font-weight="700" fill="#ffffff">${initials}</text>
            </svg>
        `;
        return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
    };

    const resolveAvatar = () => {
        const avatar = String(user.avatar || "").trim();
        if (avatar) {
            if (/^(https?:|data:|\/|\.{1,2}\/)/.test(avatar) || avatar.startsWith("assets/")) return avatar.startsWith("assets/") ? `../${avatar}` : avatar;
            return `../assets/images/${avatar.replace(/^\/+/, "")}`;
        }
        return buildAvatar(user.name || "", user.id || user.name || "");
    };

    const updateAvatarPreview = () => {
        if (!profileAvatarPreview) return;
        const file = profileAvatarFile?.files?.[0];
        if (file) {
            profileAvatarPreview.src = URL.createObjectURL(file);
            return;
        }
        profileAvatarPreview.src = resolveAvatar();
    };

    const updateUser = async (updatedFields) => {
        const result = await request(`/users/${user.id}`, "PATCH", updatedFields);
        const updatedUser = { ...user, ...updatedFields, role: result.role || user.role, avatar: result.avatar || updatedFields.avatar || user.avatar };
        user = updatedUser;
        localStorage.setItem("user", JSON.stringify(updatedUser));
        localStorage.setItem("role", updatedUser.role);
        return updatedUser;
    };

    const uploadAvatar = async () => {
        if (!profileAvatarFile?.files?.length) return null;
        const formData = new FormData();
        formData.append("avatar", profileAvatarFile.files[0]);
        return request(`/users/${user.id}/avatar`, "POST", formData);
    };

    const syncAvatar = () => {
        if (profileAvatarPreview) {
            profileAvatarPreview.src = resolveAvatar();
        }
    };

    const profileForm = document.getElementById("editProfileForm");
    if (profileForm) {
        profileForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const updatedFields = {};
            const newName = nameInput.value.trim();
            const newEmail = emailInput.value.trim();

            if (newName && newName !== user.name) updatedFields.name = newName;
            if (newEmail && newEmail !== user.email) updatedFields.email = newEmail;

            try {
                if (Object.keys(updatedFields).length > 0) {
                    await updateUser(updatedFields);
                }

                if (profileAvatarFile?.files?.length) {
                    const avatarResult = await uploadAvatar();
                    if (avatarResult?.avatar) {
                        await updateUser({ avatar: avatarResult.avatar });
                    }
                    profileAvatarFile.value = "";
                }

                if (!Object.keys(updatedFields).length && !profileAvatarFile?.files?.length) {
                    alert("Ви не внесли жодних змін.");
                    return;
                }

                syncAvatar();
                alert("Профіль успішно оновлено!");
                window.location.reload();
            } catch (error) {
                alert(error.message || "Не вдалося оновити профіль.");
            }
        });
    }

    if (profileAvatarFile) {
        profileAvatarFile.addEventListener("change", () => {
            updateAvatarPreview();
        });
    }

    const formatDate = (value) => {
        if (!value) return "";
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return String(value);
        return date.toLocaleString("uk-UA", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    const statusLabel = (status) => {
        const value = String(status || "pending").toLowerCase();
        if (value === "completed") return "Виконано";
        if (value === "confirmed") return "Підтверджено";
        if (value === "canceled") return "Скасовано";
        return "В очікуванні";
    };

    const loadHistory = async () => {
        if (!bookingsList) return;

        try {
            const bookings = await request(`/bookings/user/${user.id}`);

            if (!bookings || bookings.length === 0) {
                bookingsList.innerHTML = "<p class='no-data'>У вас ще немає записів.</p>";
                return;
            }

            bookingsList.innerHTML = bookings.map((booking) => {
                const statusClass = booking.status === "completed"
                    ? "status-completed"
                    : booking.status === "confirmed"
                        ? "status-confirmed"
                        : booking.status === "canceled"
                            ? "status-canceled"
                            : "status-pending";

                return `
                    <article class="booking-history-item">
                        <div class="booking-header">
                            <span class="service-name">${escapeHtml(booking.service_name || "Послуга")}</span>
                            <span class="badge ${statusClass}">${statusLabel(booking.status)}</span>
                        </div>
                        <div class="booking-details">
                            <span>Дата: ${escapeHtml(formatDate(booking.created_at))}</span>
                        </div>
                        <div class="master-info">Майстер: ${escapeHtml(booking.master_name || booking.master_id)}</div>
                    </article>
                `;
            }).join("");
        } catch (error) {
            console.error("History loading error:", error);
            bookingsList.innerHTML = "<p class='error-text'>Історія записів наразі недоступна.</p>";
        }
    };

    const loadMailBox = async () => {
        if (!mailNotifications) return;

        try {
            const [bookings, feedbacks] = await Promise.all([
                request(`/bookings/user/${user.id}`),
                request(`/feedback?client_id=${user.id}`),
            ]);

            const feedbackBookingIds = new Set((feedbacks || []).map((item) => String(item.booking_id)));
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
                && !feedbackBookingIds.has(String(booking.id))
            ));

            if (eligible.length === 0) {
                mailNotifications.innerHTML = `
                    <article class="home-feature">
                        <strong>Пошта</strong>
                        <span>Нових запрошень на відгук поки немає.</span>
                    </article>
                `;
                return;
            }

            mailNotifications.innerHTML = eligible.map((booking) => {
                const completedAt = booking.updated_at ? new Date(booking.updated_at).getTime() : Date.now();
                const hoursSince = Math.max(0, (Date.now() - completedAt) / 36e5);
                const ready = hoursSince >= 24;
                const note = ready
                    ? "Ваш запис готовий для відгуку. Натисніть кнопку нижче і залиште оцінку від 1 до 5 та коментар."
                    : `Запрошення на відгук буде надіслано приблизно через ${Math.ceil(24 - hoursSince)} год.`;

                return `
                    <article class="home-feature">
                        <strong>Лист на відгук</strong>
                        <span>${note}</span>
                        ${ready ? `<a class="btn-outline" style="margin-top:12px;" href="feedback.html?booking_id=${encodeURIComponent(booking.id)}">Залишити відгук</a>` : ""}
                    </article>
                `;
            }).join("");
        } catch (error) {
            console.error("Mailbox loading error:", error);
            mailNotifications.innerHTML = "<p class='error-text'>Не вдалося завантажити пошту.</p>";
        }
    };

    if (profileAvatarPreview) {
        updateAvatarPreview();
    }

    await loadHistory();
    await loadMailBox();
});
