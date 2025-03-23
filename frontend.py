from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from bson import ObjectId
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client["productiveapp"]
users_collection = db["users"]
tasks_collection = db["tasks"]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# FastAPI app
app = FastAPI()

# CORS Middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = users_collection.find_one({"username": username})
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@app.post("/signup")
def signup(username: str, password: str):
    if users_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_password = get_password_hash(password)
    users_collection.insert_one({"username": username, "password": hashed_password})
    return {"message": "User created successfully"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_collection.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/tasks")
async def create_task(task: dict, user: dict = Depends(get_current_user)):
    task["user"] = user["username"]
    task["created_at"] = datetime.utcnow()
    tasks_collection.insert_one(task)
    return {"message": "Task added successfully"}

@app.get("/tasks")
async def get_tasks(user: dict = Depends(get_current_user)):
    tasks = list(tasks_collection.find({"user": user["username"]}, {"_id": 0}))
    return {"tasks": tasks}
