import os
import requests
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from db import get_db, get_users_collection
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

security = HTTPBearer()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 60

db = get_db()
users = get_users_collection(db)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    email: EmailStr

def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_SECONDS):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

@app.get("/api/protected")
def protected_route(payload=Depends(verify_token)):
    return {"message": f"Hello, {payload['email']}! This is a protected route."}

@app.post("/api/signup")
def signup(user: UserIn):
    if users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(user.password)
    users.insert_one({"email": user.email, "password": hashed_password})
    token = create_access_token({"email": user.email})
    return {"success": True, "token": token}

@app.post("/api/login")
def login(user: UserIn):
    db_user = users.find_one({"email": user.email})
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"email": user.email})
    return {"success": True, "token": token}

@app.post("/api/chat")
def chat_with_gemini(payload: dict):
    messages = payload.get("messages", [])
    user_message = messages[-1]["content"] if messages else ""
    gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY
    gemini_payload = {
        "contents": [{"parts": [{"text": user_message}]}]
    }
    response = requests.post(gemini_url, json=gemini_payload)
    if response.status_code == 200:
        gemini_data = response.json()
        gemini_text = gemini_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return {"content": gemini_text}
    else:
        return {"content": "Sorry, Gemini API error."}

@app.get("/api/dashboard-data")
def get_dashboard_data():
    data = [
        {"id": 1, "name": "Alice", "score": 95},
        {"id": 2, "name": "Bob", "score": 88},
        {"id": 3, "name": "Charlie", "score": 92}
    ]
    return {"rows": data}

# Health check endpoint for MongoDB connection
@app.get("/api/db-health")
def db_health():
    try:
        db = get_db()
        db.command('ping')
        return {"status": "connected"}
    except Exception as e:
        return {"status": "error", "details": str(e)}