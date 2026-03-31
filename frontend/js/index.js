document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("access_token");
    const userStr = localStorage.getItem("user");
    
    const guestButtons = document.getElementById("guestButtons");
    const userButtons = document.getElementById("userButtons");
    const adminLink = document.getElementById("adminLink");
    const masterLink = document.getElementById("masterLink");
    const navLinks = document.querySelector(".nav-links");

    let userRole = null;

    if (token && userStr) {
        const user = JSON.parse(userStr);
        userRole = user.role;

        if (userRole === "admin") {
            window.location.href = "pages/admin.html";
            return;
        }

        if (guestButtons) guestButtons.style.display = "none";
        if (userButtons) userButtons.style.display = "flex"; 

        if (userButtons && !document.querySelector(".user-greeting")) {
            userButtons.insertAdjacentHTML('afterbegin', 
                `<span class="user-greeting" style="margin-right:15px; color:white; font-size:12px;">Вітаю, ${user.name}!</span>`
            );
        }

        if (userRole === "admin" && adminLink) {
            adminLink.style.display = "inline-block";
        } else if (userRole === "master" && masterLink) {
            masterLink.style.display = "inline-block";
        } else if (userRole === "client") {
            if (!document.getElementById("profileLink")) {
                navLinks.insertAdjacentHTML('beforeend', 
                    `<a href="pages/profile.html" id="profileLink" style="color:#d4af37; font-weight:bold; margin-left:20px;">ОБЛІКОВИЙ ЗАПИС</a>`
                );
            }
        }

    } else {
        if (guestButtons) guestButtons.style.display = "flex";
        if (userButtons) userButtons.style.display = "none";
        if (adminLink) adminLink.style.display = "none";
        if (masterLink) masterLink.style.display = "none";
    }

    const heroBtn = document.getElementById("heroBookingBtn");
    if (heroBtn) {
        heroBtn.onclick = (e) => {
            e.preventDefault();
            if (!token) {
                alert("Будь ласка, увійдіть у систему!");
                window.location.href = "pages/login.html";
            } else if (userRole === "client") {
                window.location.href = "pages/booking.html";
            } else {
                alert("Запис доступний тільки для клієнтів!");
            }
        };
    }
});

window.logout = function() {
    localStorage.clear();
    window.location.href = "index.html";
};