from fastapi.testclient import TestClient
from .main import api
from .auth.model import RegisterUserRequest

client = TestClient(api)

def test_register_user_already_exists():
    request = RegisterUserRequest(
        username="new_user_test",
        password="test12345",
        balance=5000
    )

    response = client.post("/register/", json=request.model_dump())
    assert response.status_code == 409
    response_detail = response.json()["detail"]
    assert response_detail == "Username has already exists"

def test_login_user():
    response = client.post("/login/", data={
        "username": "new_user_test",
        "password": "test12345"
    })
    assert response.status_code == 202
    token_data = response.json()
    assert "create_access" in token_data
    assert token_data["token_type"] == "bearer"

def test_login_username_invalid():
    response = client.post("/login/", data={
        "username" : "random_test",
        "password" : "random_test"
    })

    assert response.status_code == 400
    response_detail = response.json()["detail"]
    assert response_detail == "Username/Password is invalid!"
def test_login_password_invalid():
    response = client.post("/login/", data={
        "username" : "new_user_test",
        "password" : "random_test"
    })

    assert response.status_code == 400
    response_detail = response.json()["detail"]
    assert response_detail == "Username/Password is invalid!"

# def test_create_expense():
