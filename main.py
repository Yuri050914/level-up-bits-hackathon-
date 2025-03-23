from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv
from passlib.context import CryptContext  # For password hashing

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client["productiveapp"]
users_collection = db["users"]
tasks_collection = db["tasks"]

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI app
app = FastAPI()

# Signup with Password Hashing
@app.post("/signup")
def signup(username: str, password: str):
    if users_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = pwd_context.hash(password)  # Hash password
    users_collection.insert_one({"username": username, "password": hashed_password})
    return {"message": "User created successfully"}

# Login with Password Verification
@app.post("/login")
def login(username: str, password: str):
    user = users_collection.find_one({"username": username})
    if not user or not pwd_context.verify(password, user["password"]):  # Verify hashed password
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"message": "Login successful"}

# Add Task
@app.post("/tasks")
def create_task(username: str, task: str):
    task_data = {"username": username, "task": task}
    tasks_collection.insert_one(task_data)
    return {"message": "Task added successfully"}

# Get Tasks with `_id` Converted
@app.get("/tasks/{username}")
def get_tasks(username: str):
    tasks = list(tasks_collection.find({"username": username}, {"_id": 1, "task": 1}))
    
    # Convert ObjectId to string
    for task in tasks:
        task["_id"] = str(task["_id"])

    return {"tasks": tasks}
