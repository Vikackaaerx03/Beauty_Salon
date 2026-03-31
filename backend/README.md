# Beauty Salon

## Опис проєкту

Beauty Salon — це вебзастосунок для автоматизації роботи салону краси.
Система підтримує ролі:
- гість — перегляд каталогу послуг і майстрів;
- клієнт — запис на послугу, перегляд бронювань, оплата, відгуки;
- майстер — перегляд власного розкладу та виконаних/запланованих записів;
- адміністратор — керування даними системи.

Проєкт реалізований як окремий backend на FastAPI + frontend на HTML/CSS/JavaScript.
Дані зберігаються в MongoDB.

---

## Основний функціонал

### Гість
- перегляд каталогу послуг;
- перегляд списку майстрів;
- сортування майстрів за ім'ям або рейтингом;
- фільтрація за майстром або послугою.

### Клієнт
- реєстрація та авторизація;
- перегляд доступних слотів майстрів;
- запис на послугу;
- перегляд власних бронювань;
- оплата послуги;
- залишення відгуку після надання послуги.

### Майстер
- перегляд власного профілю;
- перегляд власного розкладу;
- перегляд зайнятих і вільних слотів;
- позначення виконаних робіт.

### Адміністратор
- перегляд записів клієнтів;
- зміна або скасування записів;
- керування платежами;
- базове адміністрування даних у системі.

---

## Логічна модель (сутності)

- **User** — користувач системи (`guest`, `client`, `admin`, `master`)
  - поля: `name`, `email`, `role`, `rating`, `services_offered`, `created_at`, `password_hash`
- **Service** — послуга
  - поля: `name`, `description`, `price`, `duration_minutes`
- **Timeslot / Schedule** — слот майстра
  - поля: `master_id`, `start`, `end`, `status`, `booking_id`
- **Booking** — бронювання
  - поля: `client_id`, `master_id`, `service_id`, `timeslot_id`, `status`, `created_at`, `updated_at`
- **Payment** — оплата
  - поля: `booking_id`, `amount`, `method`, `status`, `paid_at`
- **Feedback** — відгук
  - поля: `booking_id`, `client_id`, `master_id`, `rating`, `comment`, `created_at`

---

## Фізична модель (MongoDB)

Колекції:
- `users`
- `services`
- `schedules`
- `bookings`
- `payments`
- `feedback`

Індекси створюються під час запуску застосунку в `app/db/database.py`.

---

## Архітектура проєкту

Проєкт реалізовано за багатошаровою моделлю:

- **API layer** — `backend/app/routers/*`
- **Service layer** — `backend/app/services/*`
- **Repository layer** — `backend/app/repositories/*`
- **Models / Schemas** — `backend/app/schemas/*`
- **Database config** — `backend/app/db/*`
- **Core config/security** — `backend/app/core/*`

Frontend розташований окремо в папці `frontend/`.

---

## Структура проєкту

```text
Beauty_Salon/
|-- backend/
|   |-- app/
|   |   |-- core/
|   |   |-- db/
|   |   |-- repositories/
|   |   |-- routers/
|   |   |-- schemas/
|   |   |-- services/
|   |-- seed/
|   |-- requirements.txt
|   |-- README.md
|-- frontend/
|   |-- css/
|   |-- js/
|   |-- pages/
|   |-- index.html
|-- docker/
|   |-- docker-compose.yml
|   |-- Dockerfile
```

---

## Технології

### Backend
- Python
- FastAPI
- Pydantic
- Pydantic Settings
- PyMongo
- Uvicorn
- JWT auth

### Frontend
- HTML5
- CSS3
- JavaScript

### Database
- MongoDB

### Інструменти
- Docker
- Swagger UI
- pytest

---

## Конфігурація

Застосунок використовує `.env` у папці `backend/`.

Приклад змінних:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=beauty_salon_db
SECRET_KEY=super_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Налаштування зчитуються через `backend/app/core/config.py`.

---

## Запуск проєкту

### 1. Запуск MongoDB через Docker

Перейти в папку `docker/`:

```powershell
cd "C:\Console\visual studio code\python\3 курс\3 курс 2 семестр\Progect_Beauty_Salon1\Beauty_Salon\docker"
```

Запустити контейнери:

```powershell
docker compose up -d
```

### 2. Запуск backend

Перейти в `backend/`:

```powershell
cd "C:\Console\visual studio code\python\3 курс\3 курс 2 семестр\Progect_Beauty_Salon1\Beauty_Salon\backend"
```

Якщо є віртуальне середовище:

```powershell
.venv\Scripts\activate
```

Встановити залежності:

```powershell
pip install -r requirements.txt
```

Запустити сервер:

```powershell
uvicorn app.main:app --reload
```

Backend буде доступний тут:
- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

### 3. Запуск frontend

В іншому терміналі перейти в `frontend/`:

```powershell
cd "C:\Console\visual studio code\python\3 курс\3 курс 2 семестр\Progect_Beauty_Salon1\Beauty_Salon\frontend"
```

Запустити простий сервер:

```powershell
python -m http.server 4173
```

Frontend буде доступний тут:
- головна сторінка: `http://127.0.0.1:4173`
- адмінка: `http://127.0.0.1:4173/pages/admin.html`

---

## Роути API

### Auth
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Users
- `GET /users`
- `GET /users/{user_id}`
- `POST /users`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`

### Services
- `GET /services`
- `GET /services/{service_id}`
- `POST /services`
- `PATCH /services/{service_id}`
- `DELETE /services/{service_id}`

### Schedules
- `GET /schedules`
- `GET /schedules/{timeslot_id}`
- `POST /schedules`
- `PATCH /schedules/{timeslot_id}`
- `DELETE /schedules/{timeslot_id}`

### Bookings
- `GET /bookings`
- `POST /bookings`
- `DELETE /bookings/{booking_id}`

### Payments
- `GET /payments`
- `GET /payments/{payment_id}`
- `POST /payments`
- `PATCH /payments/{payment_id}`
- `DELETE /payments/{payment_id}`

### Feedback
- `GET /feedback`
- `GET /feedback/{feedback_id}`
- `POST /feedback`
- `DELETE /feedback/{feedback_id}`

---

## Seed-дані

Файли прикладів лежать у папці:

```text
backend/seed/
```

Приклади файлів:
- `users.json`
- `services.json`
- `schedules.json`
- `bookings.json`
- `payments.json`
- `feedback.json`

### Імпорт у MongoDB (через Docker)

```powershell
docker cp backend/seed/users.json beauty-mongo:/tmp/users.json
docker exec -it beauty-mongo mongoimport --db beauty_salon_db --collection users --file /tmp/users.json --jsonArray --drop
```

Аналогічно для інших колекцій.

> Паролі в `users.json` не зберігаються у відкритому вигляді, а лише у вигляді хешів.

---

## Тестові акаунти

У seed-даних використовуються тестові адреси формату:
- `@beauty.local`

Наприклад:
- `victoria.roslav@beauty.local` — адміністратор
- `olena.hryniuk@beauty.local` — майстер
- `kateryna.ivanova@beauty.local` — клієнт

Ці адреси зручні для локального тестування.

---

## Як подивитися базу даних

Якщо MongoDB запущена в Docker:

```powershell
docker exec -it beauty-mongo mongosh
```

Далі всередині `mongosh`:

```javascript
show dbs
use beauty_salon_db
show collections
```

Кількість документів у всіх колекціях:

```javascript
db.getCollectionNames().forEach(n => print(n, db.getCollection(n).countDocuments()))
```

Подивитися записи в колекції:

```javascript
db.users.find().pretty()
db.services.find().pretty()
db.schedules.find().pretty()
db.bookings.find().pretty()
db.payments.find().pretty()
db.feedback.find().pretty()
```

---

## Тестування

Для запуску тестів:

```powershell
cd "C:\Console\visual studio code\python\3 курс\3 курс 2 семестр\Progect_Beauty_Salon1\Beauty_Salon\backend"
pytest app/utils/helpers.py -q
```

---

## Особливості реалізації

- JWT-аутентифікація
- хешування паролів
- розмежування доступу за ролями
- робота з MongoDB через PyMongo
- Swagger/OpenAPI документація
- фронтенд винесений окремо від backend
- підтримка кирилиці в інтерфейсі й даних

---

## Примітки

- Якщо сторінки не відкриваються, перевірити, чи одночасно запущені backend і frontend.
- Якщо не підтягуються дані, перевірити токен у `localStorage` та чи користувач авторизований.
- Якщо MongoDB порожня, спочатку треба імпортувати seed-дані.
- Якщо з'являються проблеми з кодуванням, переконатися, що файли збережені в UTF-8.
