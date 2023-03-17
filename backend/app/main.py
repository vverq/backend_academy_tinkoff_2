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
from sqlalchemy.orm import Session

from app.connection_manager import ConnectionManager
from app.core.config import settings
from app.schemas import User, Friends

from backend.app import crud, models, schemas
from .database import SessionLocal, engine

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


def authenticate_user(email: str, password: str, db: Session):
    user_password = crud.get_user_password(db, email)
    if user_password:
        if password_context.verify(password, user_password[0]):
            return crud.get_user_by_email(db, email)
    return False


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("username")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    user = crud.get_user_by_email(db, email)
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
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "token": jwt.encode(
            {"email": user.email}, JWT_SECRET, algorithm=JWT_ALGORITHM
        )
    }


# todo fix update password
@app.put(
    "/users/{user_id}", tags=["user"], description="Update user, who already exists"
)
async def update_user(user_id: UUID, new_user: User, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if user:
        return crud.update_user(db, user_id, new_user)
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/users/{user_id}", tags=["user"], description="Get user by id")
async def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/users/", tags=["users"], description="Get all users", response_model=list[schemas.User])
async def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.post("/users/friends/", tags=["friendship"], description="Create friendship between user1 and user2 by their ids")
async def create_friends(friends: Friends, db: Session = Depends(get_db)):
    first_id_exists = crud.get_user(db, friends.id_friend_one)
    second_id_exists = crud.get_user(db, friends.id_friend_two)
    if first_id_exists and second_id_exists:
        return crud.create_friendship(db, friends)
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
async def create_chat(friend_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = crud.get_user(db, friend_id)
    if user:
        friends = crud.find_friendship(db, friend_id, user.id)
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
