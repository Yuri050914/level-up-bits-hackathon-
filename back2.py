from fastapi import FastAPI, HTTPException # type: ignore
from pymongo import MongoClient # type: ignore
from bson import ObjectId # type: ignore
import os
from dotenv import load_dotenv # type: ignore

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client["productiveapp"]
users_collection = db["users"]
tasks_collection = db["tasks"]

# FastAPI app
app = FastAPI()

# Signup (Basic)
@app.post("/signup")
def signup(username: str, password: str):
    if users_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    users_collection.insert_one({"username": username, "password": password})
    return {"message": "User created successfully"}

# Login (Basic)
@app.post("/login")
def login(username: str, password: str):
    user = users_collection.find_one({"username": username, "password": password})
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"message": "Login successful"}

# Add Task (No Auth)
@app.post("/tasks")
def create_task(username: str, task: str):
    task_data = {"username": username, "task": task}
    tasks_collection.insert_one(task_data)
    return {"message": "Task added successfully"}

# Get Tasks (No Auth)
@app.get("/tasks/{username}")
def get_tasks(username: str):
    tasks = list(tasks_collection.find({"username": username}, {"_id": 0}))
    return {"tasks": tasks}
