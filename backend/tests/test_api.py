from uuid import UUID
import requests
from app.main import password_context

URL = "http://0.0.0.0:5000"


def test_get_empty_users():
    response = requests.get(f"{URL}/users/")
    assert response.status_code == 200
    assert response.json() == []


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
    ids = [
        requests.post(f"{URL}/users/",  json=users[0]).json(),
        requests.post(f"{URL}/users/", json=users[1]).json(),
    ]
    response = requests.get(f"{URL}/users/")
    assert response.status_code == 200
    new_users = response.json()
    assert len(new_users) == len(users)
    for i, new_user in enumerate(new_users):
        assert new_user["id"] == ids[i]
        assert new_user["name"] == users[i]["name"]
        assert new_user["age"] == users[i]["age"]
        assert new_user["description"] == users[i]["description"]
        assert new_user["email"] == users[i]["email"]
        assert new_user["password"] != users[i]["password"]


def test_hashing_passwords():
    user = {
        "name": "Ivan1",
        "age": 22,
        "description": "I like travelling",
        "email": "kek@gmail.com",
        "password": "123",
    }
    response = requests.post(f"{URL}/users/",  json=user)
    password = UUID(response.json(), version=4)
    assert password_context.hash(user["password"]) != password


def test_get_user_by_id():
    user1 = {
        "name": "Ivan",
        "age": 22,
        "description": "I like travelling",
        "email": "qwerty@gmail.com",
        "password": "1",
    }
    user2 = {
        "name": "Elena",
        "age": 21,
        "description": ":))",
        "email": "pirozhok1@yandex.ru",
        "password": "kek",
    }
    user3 = {
        "name": "Masha",
        "age": 23,
        "description": "Practice makes perfect!",
        "email": "masha@ya.ru",
        "password": "lol8",
    }
    requests.post(f"{URL}/users/", json=user1).json()
    id2 = requests.post(f"{URL}/users/", json=user2).json()
    requests.post(f"{URL}/users/", json=user3).json()
    response = requests.get(f"{URL}/users/{id2}")
    user2["id"] = id2
    assert response.status_code == 200
    new_user = response.json()
    assert new_user["name"] == user2["name"]
    assert new_user["age"] == user2["age"]
    assert new_user["description"] == user2["description"]
    assert new_user["email"] == user2["email"]


def test_update_user():
    user = {
        "name": "Ivan",
        "age": 22,
        "description": "I like travelling",
        "email": "vanya2015@gmail.com",
        "password": "123"
    }
    updated_user = {
        "name": "Ivan",
        "age": 23,
        "description": "I like travelling and cats",
        "email": "vanya001@gmail.com",
        "password": "123",
        "login_date": None,
    }
    id = requests.post(f"{URL}/users/", json=user).json()
    updated_user["id"] = id
    response = requests.put(f"{URL}/users/{id}", json=updated_user)
    assert response.status_code == 200
    assert response.json() == updated_user
    response_get_updated_user = requests.get(f"{URL}/users/{id}")
    assert response_get_updated_user.status_code == 200
    assert response_get_updated_user.json() == updated_user


def test_create_user():
    response = requests.post(
        f"{URL}/users/",
        json={
            "name": "Ivan",
            "age": 22,
            "description": "I like travelling",
            "email": "not_ivan@gmail.com",
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
        "email": "katya0102@gmail.com",
        "password": "1235",
    }
    user2 = {
        "name": "Anna",
        "age": 21,
        "description": ":))",
        "email": "anya_2001@yandex.ru",
        "password": "qwerty1",
    }
    id1 = requests.post(f"{URL}/users/", json=user1).json()
    id2 = requests.post(f"{URL}/users/", json=user2).json()
    token = requests.post(
        f"{URL}/users/login/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        json="grant_type=&username=anya_2001@yandex.ru&password=qwerty1&scope=&client_id=&client_secret=",
    ).json()["token"]
    user1["id"] = id1
    user2["id"] = id2
    response = requests.post(
        f"{URL}/users/friends/",
        headers={"Authorization": f"Bearer {token}"},
        json={"id_friend_one": id1, "id_friend_two": id2},
    )
    assert response.status_code == 200
    response = response.json()
    assert response["friend_id_one"] == id1
    assert response["friend_id_two"] == id2
