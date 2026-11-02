
from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ab-testing-decision-engine",
    }


def test_simulate_and_analyze_endpoint():
    response = client.post(
        "/simulate-and-analyze",
        json={
            "n_users": 5000,
            "true_control_rate": 0.10,
            "true_lift": 0.03,
            "n_days": 7,
            "seed": 42,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["verdict"] in ["SHIP", "KILL", "HOLD", "NEEDS_MORE_DATA"]
    assert isinstance(data["reasoning"], list)
    assert isinstance(data["srm_check_passed"], bool)
    assert isinstance(data["sequential_safe_to_stop"], bool)


def test_invalid_alpha_is_rejected():
    response = client.post(
        "/simulate-and-analyze",
        json={
            "n_users": 5000,
            "alpha": 1.5,
        },
    )

    # The decision engine should reject this invalid significance level.
    assert response.status_code == 422


def test_invalid_user_count_is_rejected():
    response = client.post(
        "/simulate-and-analyze",
        json={
            "n_users": 0,
        },
    )

    # The simulator should reject an invalid user count.
    assert response.status_code == 422


def test_cors_allows_configured_frontend():
    response = client.options(
        "/simulate-and-analyze",
        headers={
            "Origin": "http://localhost:5500",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5500"


def test_cors_rejects_unconfigured_frontend():
    response = client.options(
        "/simulate-and-analyze",
        headers={
            "Origin": "https://untrusted-example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400

def test_internal_errors_are_hidden_from_api_users(monkeypatch):
    import api.app as api_module

    def simulate_failure(config):
        raise RuntimeError("Sensitive internal database error")

    monkeypatch.setattr(
        api_module,
        "simulate_experiment",
        simulate_failure,
    )

    response = client.post(
        "/simulate-and-analyze",
        json={
            "n_users": 5000,
            "true_control_rate": 0.10,
            "true_lift": 0.02,
            "n_days": 7,
            "seed": 42,
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "An internal error occurred while analyzing the experiment."
    )
    assert "Sensitive internal database error" not in response.text
