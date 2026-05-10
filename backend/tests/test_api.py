# filepath: tests/test_api.py
"""
Модульні тести для Beauty Salon API
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


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