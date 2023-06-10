import random

import requests
from faker import Faker

ENDPOINT = "http://localhost:5000/user/{}"
ENDPOINT2 = "http://localhost:5000/users"
ENDPOINT3 = "http://localhost:5000/users1"


POST_ENDPOINT = ""


def main():
    f = Faker()
    while True:
        rand = random.randint(0, 4)
        if rand == 0:
            _ = requests.get(ENDPOINT.format(random.randint(0, 100)))
        elif rand == 1:
            _ = requests.get(ENDPOINT2)
        elif rand == 2:
            _ = requests.get(ENDPOINT3)
        # elif rand == 3:
        #     _ = requests.exceptions.HTTPError
        else:
            payload = {
                "name": f.name(),
                "age": random.randint(18,60),
                "description": f.text(),
                "email": f.email(),
                "password": f.password(),
            }
            _ = requests.post(ENDPOINT2, json=payload)


main()