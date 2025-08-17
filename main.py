# Example usage in a chat endpoint:
# @app.post("/api/chat")
# def chat_endpoint(request: ChatRequest):
#     ...existing code to generate assistant_response...
#     cleaned_response = clean_assistant_prefix(assistant_response)
#     return {"role": "assistant", "content": cleaned_response}
def clean_assistant_prefix(text: str) -> str:
    if text.lower().startswith("assistant:"):
        return text[len("assistant:"):].lstrip()
    return text
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta


security = HTTPBearer()

# Define FastAPI app instance
app = FastAPI()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
# JWT setup
@app.get("/api/protected")
def protected_route(payload=Depends(verify_token)):
    return {"message": f"Hello, {payload['email']}! This is a protected route."}

# CORS for Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chatbot-ui-frontend.vercel.app","http://localhost:3000"],  # update to your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
client = MongoClient("mongodb+srv://vishwamshah007:2FEdUuBbSNY8TI1r@cluster0.5jhbvkx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["chatbot"]
users = db["users"]

# JWT setup
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 60

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