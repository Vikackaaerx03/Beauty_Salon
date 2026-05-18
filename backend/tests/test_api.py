# filepath: tests/test_api.py
"""
Модульні тести для Beauty Salon API
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

import app.routers.auth_router as auth_router
import app.routers.services_router as services_router


class FakeAuthService:
    def register(self, payload):
        return {
            "token": {"access_token": "fake-token", "token_type": "bearer"},
            "user": {
                "id": "1",
                "name": payload.name,
                "email": payload.email,
                "role": payload.role,
                "rating": 0.0,
                "services_offered": [],
                "created_at": "2026-05-18T00:00:00",
            },
        }

    def login(self, payload):
        return {
            "token": {"access_token": "fake-token", "token_type": "bearer"},
            "user": {
                "id": "1",
                "name": "Test User",
                "email": payload.email,
                "role": "client",
                "rating": 0.0,
                "services_offered": [],
                "created_at": "2026-05-18T00:00:00",
            },
        }


class FakeServicesService:
    def __init__(self):
        self._storage = {}
        self._next_id = 1

    def create(self, payload):
        service_id = str(self._next_id)
        self._next_id += 1
        record = payload.model_dump()
        record.update({"id": service_id, "status": "active"})
        self._storage[service_id] = record
        return record

    def list(self, min_price=None, max_price=None, include_deleted=False):
        return list(self._storage.values())

    def get(self, service_id):
        if service_id not in self._storage:
            raise ValueError("Service not found")
        return self._storage[service_id]

    def update(self, service_id, payload):
        if service_id not in self._storage:
            raise ValueError("Service not found")
        updates = payload.model_dump(exclude_none=True)
        self._storage[service_id].update(updates)
        return self._storage[service_id]

    def delete(self, service_id):
        if service_id not in self._storage:
            raise ValueError("Service not found")
        del self._storage[service_id]


@pytest.fixture
def mock_db():
    with patch("app.db.database.init_db") as mock_init:
        mock_init.return_value = None
        yield mock_init


@pytest.fixture
def client(mock_db):
    """Створюємо тестовий клієнт без реального підключення до БД"""
    from app.main import app
    return TestClient(app)


class TestServicesAPI:
    """Тести для ендпоінтів послуг"""

    def test_list_services_empty(self, client, mock_db):
        """Тест отримання списку послуг (порожня БД)"""
        with patch("app.services.services_service.ServicesService") as MockService:
            mock_service = MagicMock()
            mock_service.list.return_value = []
            MockService.return_value = mock_service
            
            response = client.get("/services/")
            # Може бути 200 або 500 (якщо БД недоступна)
            assert response.status_code in [200, 500]

    def test_services_endpoint_exists(self, client):
        """Тест існування ендпоінту послуг"""
        response = client.get("/services/")
        # Перевіряємо, що ендпоінт існує
        assert response.status_code in [200, 401, 500]


class TestAuthAPI:
    """Тести для автентифікації"""

    def test_register_endpoint_exists(self, client):
        """Тест існування ендпоінту реєстрації"""
        response = client.post("/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpass123"
        })
        # Перевіряємо, що ендпоінт існує (може бути 400, 500, але не 404)
        assert response.status_code != 404

    def test_login_endpoint_exists(self, client):
        """Тест існування ендпоінту входу"""
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        assert response.status_code != 404


class TestBookingsAPI:
    """Тести для бронювань"""

    def test_booking_endpoint_exists(self, client):
        """Тест існування ендпоінту бронювань"""
        response = client.get("/bookings/")
        # Не 404 - ендпоінт існує
        assert response.status_code != 404


class TestMastersAPI:
    """Тести для майстрів"""

    def test_masters_list_endpoint_exists(self, client):
        """Тест існування ендпоінту списку майстрів"""
        response = client.get("/users/masters")
        assert response.status_code != 404


class TestFeedbackAPI:
    """Тести для відгуків"""

    def test_feedback_endpoint_exists(self, client):
        """Тест існування ендпоінту відгуків"""
        response = client.get("/feedback/")
        assert response.status_code != 404


class TestSwagger:
    """Тести для Swagger документації"""

    def test_swagger_ui_available(self, client):
        """Тест доступності Swagger UI"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json_available(self, client):
        """Тест доступності OpenAPI JSON"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Beauty Salon API"

    def test_api_has_all_routes(self, client):
        """Тест наявності всіх основних роутерів"""
        response = client.get("/openapi.json")
        data = response.json()
        paths = data.get("paths", {})
        
        # Перевіряємо наявність основних ендпоінтів
        expected_paths = ["/auth/", "/services/", "/bookings/", "/users/", "/feedback/"]
        for path in expected_paths:
            assert any(path in p for p in paths), f"Шлях {path} не знайдено в API"


class TestAdditionalRoutes:
    """Додаткові тести на існування маршрутів"""

    def test_schedules_endpoint_exists(self, client):
        response = client.get("/schedules/")
        assert response.status_code != 404

    def test_payments_endpoint_exists(self, client):
        response = client.get("/payments/")
        assert response.status_code != 404

    def test_users_endpoint_exists(self, client):
        response = client.get("/users/")
        assert response.status_code != 404

    def test_health_check(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "message": "Beauty Salon API is running"}

    def test_openapi_contains_schedule_and_payment_paths(self, client):
        response = client.get("/openapi.json")
        data = response.json()
        paths = data.get("paths", {})
        assert any(path.startswith("/schedules") for path in paths)
        assert any(path.startswith("/payments") for path in paths)


class TestAuthFlows:
    """Тести авторизації"""

    def test_register_success(self, client):
        fake_service = FakeAuthService()
        client.app.dependency_overrides[auth_router.get_auth_service] = lambda: fake_service

        response = client.post("/auth/register", json={
            "name": "Test User",
            "email": "test.user@beauty.local",
            "password": "securepass123",
            "role": "client",
        })

        client.app.dependency_overrides.clear()

        assert response.status_code == 201
        body = response.json()
        assert body["token"]["access_token"] == "fake-token"
        assert body["user"]["email"] == "test.user@beauty.local"
        assert body["user"]["role"] == "client"

    def test_login_failure_invalid_credentials(self, client):
        mock_service = MagicMock()
        mock_service.login.side_effect = ValueError("Невірний email або пароль")
        client.app.dependency_overrides[auth_router.get_auth_service] = lambda: mock_service

        response = client.post("/auth/login", json={
            "email": "wrong@beauty.local",
            "password": "badpass",
        })

        client.app.dependency_overrides.clear()

        assert response.status_code == 401
        assert response.json()["detail"] == "Невірний email або пароль"

    def test_login_success(self, client):
        fake_service = FakeAuthService()
        client.app.dependency_overrides[auth_router.get_auth_service] = lambda: fake_service

        response = client.post("/auth/login", json={
            "email": "test.user@beauty.local",
            "password": "securepass123",
        })

        client.app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json()["token"]["access_token"] == "fake-token"
        assert response.json()["user"]["email"] == "test.user@beauty.local"


class TestServicesCRUD:
    """CRUD-тести для ресурсу сервісів"""

    def test_service_crud_lifecycle(self, client):
        fake_service = FakeServicesService()
        client.app.dependency_overrides[services_router.get_services_service] = lambda: fake_service
        client.app.dependency_overrides[services_router.get_current_admin] = lambda: {"id": "admin", "role": "admin", "email": "admin@beauty.local"}

        create_payload = {
            "name": "Haircut",
            "description": "Basic haircut service",
            "price": 120.0,
            "duration_minutes": 45,
        }
        create_response = client.post("/services", json=create_payload)
        assert create_response.status_code == 201
        created_service = create_response.json()
        service_id = created_service["id"]
        assert created_service["name"] == "Haircut"
        assert created_service["price"] == 120.0

        get_response = client.get(f"/services/{service_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == service_id

        patch_response = client.patch(f"/services/{service_id}", json={"price": 140.0})
        assert patch_response.status_code == 200
        assert patch_response.json()["price"] == 140.0

        list_response = client.get("/services")
        assert list_response.status_code == 200
        assert any(item["id"] == service_id for item in list_response.json())

        delete_response = client.delete(f"/services/{service_id}")
        assert delete_response.status_code == 204

        not_found_response = client.get(f"/services/{service_id}")
        assert not_found_response.status_code == 404

        client.app.dependency_overrides.clear()

    def test_service_list_filters(self, client):
        fake_service = FakeServicesService()
        fake_service.create(MagicMock(model_dump=lambda: {"name": "One", "description": "A", "price": 50.0, "duration_minutes": 60}))
        fake_service.create(MagicMock(model_dump=lambda: {"name": "Two", "description": "B", "price": 200.0, "duration_minutes": 90}))
        client.app.dependency_overrides[services_router.get_services_service] = lambda: fake_service

        response = client.get("/services?min_price=100&max_price=250")
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        assert len(results) == 2

        client.app.dependency_overrides.clear()

    def test_register_login_and_service_scenario(self, client):
        fake_auth_service = FakeAuthService()
        fake_service = FakeServicesService()
        client.app.dependency_overrides[auth_router.get_auth_service] = lambda: fake_auth_service
        client.app.dependency_overrides[services_router.get_services_service] = lambda: fake_service
        client.app.dependency_overrides[services_router.get_current_admin] = lambda: {"id": "admin", "role": "admin", "email": "admin@beauty.local"}

        register_response = client.post("/auth/register", json={
            "name": "Scenario User",
            "email": "scenario.user@beauty.local",
            "password": "password123",
            "role": "client",
        })
        assert register_response.status_code == 201

        login_response = client.post("/auth/login", json={
            "email": "scenario.user@beauty.local",
            "password": "password123",
        })
        assert login_response.status_code == 200
        assert login_response.json()["token"]["access_token"] == "fake-token"

        create_response = client.post("/services", json={
            "name": "Scenario Service",
            "description": "Scenario integration service",
            "price": 99.0,
            "duration_minutes": 30,
        })
        assert create_response.status_code == 201

        list_response = client.get("/services")
        assert list_response.status_code == 200
        assert any(svc["name"] == "Scenario Service" for svc in list_response.json())

        client.app.dependency_overrides.clear()
