"""
Утиліта для відправки email повідомлень
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """
    Відправляє email повідомлення клієнту
    
    Args:
        to_email: Email отримувача
        subject: Тема листа
        body: Текст листа (plain text)
        html_body: HTML версія листа (опціонально)
    
    Returns:
        True якщо email відправлено успішно
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info("Email не налаштовано. Пропускаємо відправку для %s", to_email)
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email
        
        # Додаємо plain text версію
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        # Додаємо HTML версію якщо є
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))
        
        # Підключення до SMTP сервера
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info("Email відправлено: %s", to_email)
        return True
        
    except Exception as e:
        logger.error("Помилка відправки email: %s", e)
        return False


def send_feedback_request_email(
    client_email: str,
    client_name: str,
    master_name: str,
    service_name: str,
    booking_id: str
) -> bool:
    """
    Відправляє запит на відгук після виконання послуги
    
    Args:
        client_email: Email клієнта
        client_name: Ім'я клієнта
        master_name: Ім'я майстра
        service_name: Назва послуги
        booking_id: ID запису
    """
    subject = "💅 Залиште відгук про ваш візит до салону краси"
    
    plain_body = f"""
Привіт, {client_name}!

Дякуємо, що відвідали наш салон краси!
Ми сподіваємося, що вам сподобалась послуга "{service_name}" від майстра {master_name}.

Будь ласка, залиште свій відгук про візит — це допоможе нам покращувати якість послуг.
Відгук можна залишити за посиланням: http://localhost:4173/pages/feedback.html?booking={booking_id}

Оцініть ваш досвід від 1 до 5 зірочок та залиште коментар для майстра.

Дякуємо за ваш час!
Команда Beauty Salon
"""
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #7d4e57, #d99aa2); padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .header h1 {{ color: white; margin: 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; background: #7d4e57; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #888; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💅 Beauty Salon</h1>
        </div>
        <div class="content">
            <p>Привіт, <strong>{client_name}</strong>!</p>
            <p>Дякуємо, що відвідали наш салон краси!</p>
            <p>Ми сподіваємося, що вам сподобалась послуга "<strong>{service_name}</strong>" від майстра <strong>{master_name}</strong>.</p>
            <p>Будь ласка, залиште свій відгук про візит — це допоможе нам покращувати якість послуг.</p>
            <center>
                <a href="http://localhost:4173/pages/feedback.html?booking_id={booking_id}" class="button">Залишити відгук</a>
            </center>
            <p><strong>Оцініть ваш досвід:</strong></p>
            <ul>
                <li>⭐ - Погано</li>
                <li>⭐⭐ - Задовільно</li>
                <li>⭐⭐⭐ - Добре</li>
                <li>⭐⭐⭐⭐ - Дуже добре</li>
                <li>⭐⭐⭐⭐⭐ - Відмінно</li>
            </ul>
            <p>Дякуємо за ваш час!</p>
            <p>Команда Beauty Salon</p>
        </div>
        <div class="footer">
            <p>© 2025 Beauty Salon. Усі права захищені.</p>
        </div>
    </div>
</body>
</html>
"""
    
    return send_email(client_email, subject, plain_body, html_body)