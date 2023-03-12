from uuid import UUID
from fastapi.testclient import TestClient
from app.main import app, password_context


def test_get_empty_users():
    with TestClient(app) as client:
        response = client.get("/users/")
        assert response.status_code == 200
        assert response.json() == []
        client.close()


def test_get_users():
    users = [
        {
            "name": "Ivan",
            "age": 22,
            "description": "I like travelling",
            "email": "123@gmail.com",
            "password": "123",
        },
        {
            "name": "Elena",
            "age": 21,
            "description": ":))",
            "email": "lol@yandex.ru",
            "password": "lol_1999",
        },
    ]
    with TestClient(app) as client:
        ids = [
            client.post("/users/", json=users[0]).json(),
            client.post("/users/", json=users[1]).json(),
        ]
        response = client.get("/users/")
        assert response.status_code == 200
        new_users = response.json()
        i = 0
        for user in new_users:
            assert user["id"] == ids[i]
            assert user["name"] == user["name"]
            assert user["age"] == user["age"]
            assert user["description"] == user["description"]
            assert user["email"] == user["email"]
            assert user["password"] != user["password"]
            i += 1
        client.close()


def test_hashing_passwords():
    user = {
        "name": "Ivan1",
        "age": 22,
        "description": "I like travelling",
        "email": "123@gmail.com",
        "password": "123",
    }
    with TestClient(app) as client:
        response = client.post("/users/", json=user)
        password = UUID(response.json(), version=4)
        assert password_context.hash(user["password"]) != password


def test_get_user_by_id():
    user1 = {
        "name": "Ivan",
        "age": 22,
        "description": "I like travelling",
        "email": "123@gmail.com",
        "password": "1",
    }
    user2 = {
        "name": "Elena",
        "age": 21,
        "description": ":))",
        "email": "lol@yandex.ru",
        "password": "kek",
    }
    user3 = {
        "name": "Masha",
        "age": 23,
        "description": "Practice makes perfect!",
        "email": "maria1@ya.ru",
        "password": "lol8",
    }
    with TestClient(app) as client:
        client.post("/users/", json=user1).json()
        id2 = client.post("/users/", json=user2).json()
        client.post("/users/", json=user3).json()
        response = client.get(f"/users/{id2}")
        user2["id"] = id2
        assert response.status_code == 200
        new_user = response.json()
        assert new_user["name"] == user2["name"]
        assert new_user["age"] == user2["age"]
        assert new_user["description"] == user2["description"]
        assert new_user["email"] == user2["email"]
        client.close()


def test_update_user():
    user = {
        "name": "Ivan",
        "age": 22,
        "description": "I like travelling",
        "email": "123@gmail.com",
        "password": "123",
    }
    updated_user = {
        "name": "Ivan",
        "age": 23,
        "description": "I like travelling and cats",
        "email": "1234@gmail.com",
        "password": "123",
    }
    with TestClient(app) as client:
        id = client.post("/users/", json=user).json()
        updated_user["id"] = id
        response = client.put(f"/users/{id}", json=updated_user)
        assert response.status_code == 200
        assert response.json() == updated_user
        response_get_updated_user = client.get(f"/users/{id}")
        assert response_get_updated_user.status_code == 200
        assert response_get_updated_user.json() == updated_user
        client.close()


def test_create_user():
    with TestClient(app) as client:
        response = client.post(
            "/users/",
            json={
                "name": "Ivan",
                "age": 22,
                "description": "I like travelling",
                "email": "heq@gmail.com",
                "password": "123",
            },
        )
        assert response.status_code == 200
        assert UUID(response.json(), version=4) is not None


def test_create_friendship():
    user1 = {
        "name": "Kate",
        "age": 22,
        "description": "I like travelling",
        "email": "123@gmail.com",
        "password": "123",
    }
    user2 = {
        "name": "Anna",
        "age": 21,
        "description": ":))",
        "email": "lol@yandex.ru",
        "password": "qwerty1",
    }
    with TestClient(app) as client:
        id1 = client.post("/users/", json=user1).json()
        id2 = client.post("/users/", json=user2).json()
        token = client.post(
            "/users/login/",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            json="grant_type=&username=Anna&password=qwerty1&scope=&client_id=&client_secret=",
        ).json()["token"]
        user1["id"] = id1
        user2["id"] = id2
        response = client.post(
            "/users/friends/",
            headers={"Authorization": f"Bearer {token}"},
            json={"id_friend_one": id1, "id_friend_two": id2},
        )
        assert response.status_code == 200
        response = response.json()
        assert response["id_friend_one"] == id1
        assert response["id_friend_two"] == id2
