document.addEventListener("DOMContentLoaded", () => {
    const feedbackForm = document.getElementById('feedbackForm');
    
    if (feedbackForm) {
        feedbackForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                rating: parseInt(document.getElementById('rating').value),
                comment: document.getElementById('comment').value
            };
            try {
                await request("/feedback", "POST", data); 
                alert("Дякуємо за ваш відгук! Ваша думка важлива для нас.");
                window.location.href = "../index.html";
            } catch (error) {
                console.error("Помилка відправки відгуку");
            }
        });
    }
});