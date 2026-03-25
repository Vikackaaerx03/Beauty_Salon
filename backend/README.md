# Beauty Salon (Backend)

## Логічна модель (сутності)

- **User (користувач)**: `guest | client | admin | master`
  - поля: `name`, `email`, `role`, `rating` (для майстрів), `services_offered` (id послуг), `created_at`, `password_hash`
- **Service (послуга)**
  - поля: `name`, `description`, `price`, `duration_minutes`
- **Timeslot / Schedule (таймслот майстра)**
  - поля: `master_id`, `start`, `end`, `status: free|booked`, `booking_id`
- **Booking (запис клієнта)**
  - поля: `client_id`, `master_id`, `service_id`, `timeslot_id`, `status`, `created_at`, `updated_at`
- **Payment (оплата)**
  - поля: `booking_id`, `amount`, `method: card|cash`, `status: paid|unpaid|refunded`, `paid_at`
- **Feedback (відгук)**
  - поля: `booking_id`, `client_id`, `master_id`, `rating (1..5)`, `comment`, `created_at`

## Фізична модель (MongoDB)

Колекції: `users`, `services`, `schedules`, `bookings`, `payments`, `feedback`.

Індекси створюються на старті застосунку в `app/db/database.py:init_db()`:
- `users.email` (unique), + індекси для сортування/фільтрації по `role/name/rating`
- `services.name`, `services.price`
- `schedules.master_id + start`, `schedules.master_id + status`
- `bookings.client_id + created_at`, `bookings.master_id + created_at`, `bookings.timeslot_id` (unique, sparse)
- `payments.booking_id`, `payments.paid_at`
- `feedback.master_id + created_at`, `feedback.booking_id` (unique, sparse)

## CRUD + Dependency Injection

- Підключення до MongoDB і DI колекцій: `app/db/database.py` (через `fastapi.Depends`).
- CRUD операції: `app/repositories/*_repository.py`.
- Service layer: `app/services/*_service.py`.
- API layer (FastAPI роутери): `app/routers/*_router.py`.

## Запуск (Mongo + API)

1) Підняти MongoDB (Docker):
- перейти в `docker/`
- `docker compose up -d`

2) Запустити API:
- перейти в `backend/`
- `uvicorn app.main:app --reload`

## Як подивитися БД (mongosh)

1) Зайти в shell MongoDB (якщо Mongo у Docker):
- `docker exec -it beauty-mongo mongosh`

2) Команди всередині `mongosh`:
- `show dbs`
- `use beauty_salon_db`
- `show collections`
- кількість документів у кожній колекції:
  - `db.getCollectionNames().forEach(n => print(n, db.getCollection(n).countDocuments()))`

Важливо: у MongoDB колекції з’являються тільки після першого `insert`.

## Seed-дані (JSON)

Файли з прикладами даних лежать у `backend/seed/`.

Імпорт у Docker-контейнер (приклад):
- `docker cp backend/seed/users.json beauty-mongo:/seed/users.json`
- `docker exec -it beauty-mongo mongoimport --db beauty_salon_db --collection users --file /seed/users.json --jsonArray --drop`

Аналогічно для:
- `services.json` → `services`
- `schedules.json` → `schedules`
- `bookings.json` → `bookings`
- `payments.json` → `payments`
- `feedback.json` → `feedback`

Примітка: у `users.json` є поле `password` лише для зручності перегляду. Після імпорту краще прибрати його:
- `db.users.updateMany({}, { $unset: { password: "" } })`

## Тестування базових операцій з БД (pytest)

Тести базового CRUD і простого флоу (service → user → schedule → booking) знаходяться у `app/utils/helpers.py`.

Запуск:
- перейти в `backend/`
- `pytest app/utils/helpers.py -q`
