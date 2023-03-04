from uuid import UUID
from fastapi.testclient import TestClient
from app.main import app


def test_get_empty_users():
    with TestClient(app) as client:
        response = client.get("/users/")
        assert response.status_code == 200
        assert response.json() == {}


def test_get_users():
    user1 = {"name": "Ivan", "age": 22, "description": "I like travelling", "email": "123@gmail.com"}
    user2 = {"name": "Elena", "age": 21, "description": ":))", "email": "lol@yandex.ru"}
    with TestClient(app) as client:
        id1 = client.post("/users/", json=user1).json()
        id2 = client.post("/users/", json=user2).json()
        user1["id"] = id1
        user2["id"] = id2
        response = client.get("/users/")
        assert response.status_code == 200
        assert response.json() == {str(id1): user1, str(id2): user2}


def test_get_user_by_id():
    user1 = {"name": "Ivan", "age": 22, "description": "I like travelling", "email": "123@gmail.com"}
    user2 = {"name": "Elena", "age": 21, "description": ":))", "email": "lol@yandex.ru"}
    user3 = {"name": "Masha", "age": 23, "description": "Practice makes perfect!", "email": "maria1@ya.ru"}
    with TestClient(app) as client:
        client.post("/users/", json=user1).json()
        id2 = client.post("/users/", json=user2).json()
        client.post("/users/", json=user3).json()
        response = client.get(f"/users/{id2}")
        user2["id"] = id2
        assert response.status_code == 200
        assert response.json() == user2


def test_update_user():
    user = {"name": "Ivan", "age": 22, "description": "I like travelling", "email": "123@gmail.com"}
    updated_user = {"name": "Ivan", "age": 23, "description": "I like travelling and cats", "email": "1234@gmail.com"}
    with TestClient(app) as client:
        id = client.post("/users/", json=user).json()
        updated_user["id"] = id
        response = client.put(f"/users/{id}", json=updated_user)
        assert response.status_code == 200
        assert response.json() == updated_user
        response_get_updated_user = client.get(f"/users/{id}")
        assert response_get_updated_user.status_code == 200
        assert response_get_updated_user.json() == updated_user


def test_create_friendship():
    user1 = {"name": "Ivan", "age": 22, "description": "I like travelling", "email": "123@gmail.com"}
    user2 = {"name": "Elena", "age": 21, "description": ":))", "email": "lol@yandex.ru"}
    with TestClient(app) as client:
        id1 = client.post("/users/", json=user1).json()
        id2 = client.post("/users/", json=user2).json()
        user1["id"] = id1
        user2["id"] = id2
        response = client.post("/users/friends/", json={"id_friend_one": id1, "id_friend_two": id2})
        assert response.status_code == 200
        assert response.json() is None


def test_create_user():
    with TestClient(app) as client:
        user = {"name": "Ivan", "age": 22, "description": "I like travelling", "email": "123@gmail.com"}
        response = client.post("/users/", json=user)
        assert response.status_code == 200
        assert UUID(response.json(), version=4) is not None
