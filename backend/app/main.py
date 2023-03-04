import jwt
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    status,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

from app.connection_manager import ConnectionManager
from app.models import User, Friends
from app.core.config import settings

USERS = dict()
FRIENDS = dict()
JWT_SECRET = "secret"
JWT_ALGORITHM = "HS256"

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_application():
    _app = FastAPI(title=settings.PROJECT_NAME)

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return _app


app = get_application()


def authenticate_user(username: str, password: str):
    for user in USERS.values():
        if user.name == username:
            if password_context.verify(password, user.password):
                return user
    return False


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    for user in USERS.values():
        if user.name == username:
            return user
    raise credentials_exception


@app.post("/users/", tags=["user"], description="Create new user")
async def create_user(user: User):
    user.password = password_context.hash(user.password)
    USERS[user.id] = user
    return user.id


@app.post("/users/login", tags=["user"], description="Login user")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "token": jwt.encode(
            {"username": user.name}, JWT_SECRET, algorithm=JWT_ALGORITHM
        )
    }


@app.put(
    "/users/{user_id}", tags=["user"], description="Update user, who already exists"
)
async def update_user(user_id: UUID, user: User):
    if user_id in USERS.keys():
        USERS[user_id] = user
        return user
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/users/{user_id}", tags=["user"], description="Get user by id")
async def get_user(user_id: UUID):
    if user_id in USERS.keys():
        return USERS[user_id]
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/users/", tags=["users"], description="Get all users")
async def get_users():
    return USERS


@app.post("/users/friends/", tags=["friendship"], description="Create friendship between user1 and user2 by their ids")
async def create_friends(friends: Friends):
    if friends.id_friend_one in USERS.keys() and friends.id_friend_two in USERS.keys():
        FRIENDS[friends.id] = friends
        return
    raise HTTPException(status_code=404,
                        detail=f"User with id {friends.id_friend_one} or with id {friends.id_friend_two} not found")


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:5000/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/", tags=["chat"])
async def create_chat():
    return HTMLResponse(html)


@app.get(
    "/users/friends/chat/",
    tags=["chat"],
    description="Create a chat between two friends",
)
async def create_chat(friend_id: UUID, user: User = Depends(get_current_user)):
    if friend_id in USERS.keys():
        for friends in FRIENDS.values():
            if (
                friends.id_friend_one == friend_id and friends.id_friend_two == user.id
            ) or (
                friends.id_friend_one == user.id and friends.id_friend_two == friend_id
            ):
                return HTMLResponse(html)
            raise HTTPException(
                status_code=403, detail=f"User with id {friend_id} is not your friend"
            )
    raise HTTPException(status_code=404, detail=f"User with id {friend_id} not found")


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    manager = ConnectionManager()
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
