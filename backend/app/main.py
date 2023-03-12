from uuid import UUID

import jwt
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
from fastapi_sqlalchemy import DBSessionMiddleware, db
from sqlalchemy.orm import Session

from app.connection_manager import ConnectionManager
from app.core.config import settings
from app.schemas import User, Friends
from app.models import User as ModelUser
from app.models import Friendship as FriendshipModel

from app import crud, models, schemas
from .database import SessionLocal, engine

USERS = dict()
FRIENDS = dict()
JWT_SECRET = "secret"
JWT_ALGORITHM = "HS256"

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
    user_password = db.session.query(ModelUser.password).filter(ModelUser.name == username).first()
    if user_password:
        if password_context.verify(password, user_password):
            return db.session.query(ModelUser).filter(ModelUser.name == username).first()
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
    user = crud.get_user_by_username(username)
    if user:
        return user
    raise credentials_exception


@app.post("/users/", tags=["user"], description="Create new user")
async def create_user(user: schemas.User, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user.password = password_context.hash(user.password)
    return crud.create_user(db=db, user=user)


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
    user = db.session.query(ModelUser).filter(ModelUser.id == user_id).first()
    if user:
        db.session.query(ModelUser).filter(ModelUser.id == user_id).update({
            "name": user.name, "description": user.description, "email": user.email
        })
        db.session.commit()
        return user
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/users/{user_id}", tags=["user"], description="Get user by id")
async def get_user(user_id: UUID):
    user = db.session.query(ModelUser).filter(ModelUser.id == user_id).first()
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/users/", tags=["users"], description="Get all users", response_model=list[schemas.User])
async def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.post("/users/friends/", tags=["friendship"], description="Create friendship between user1 and user2 by their ids")
async def create_friends(friends: Friends):
    first_id_exists = bool(db.session.query(ModelUser).get(friends.id_friend_one))
    second_id_exists = bool(db.session.query(ModelUser).get(friends.id_friend_two))
    if first_id_exists and second_id_exists:
        db_friends = FriendshipModel(id=friends.id, friend_id_one=friends.id_friend_one, friend_id_two=friends.id_friend_two)
        db.session.add(db_friends)
        db.session.commit()
        return db_friends
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
            var ws = new WebSocket(`ws://0.0.0.0:5000/ws/${client_id}`);
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
    user = db.session.query(ModelUser).filter(ModelUser.id == friend_id).first()
    if user:
        friends = db.session.query(FriendshipModel).filter((
            (FriendshipModel.friend_id_one == friend_id) & (FriendshipModel.friend_id_two == user.id)) |
            (FriendshipModel.friend_id_one == user.id) & (FriendshipModel.friend_id_two == friend_id)).first()
        if friends:
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
