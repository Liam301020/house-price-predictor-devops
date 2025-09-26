# api.py — FastAPI with JWT Authentication + Prediction CRUD
import os
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, Path
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base


# ================== Config ==================
DB_URL = os.getenv("DB_URL", "sqlite:///data.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-jwt-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

app = FastAPI(title="House Price API", version="1.0")
from prometheus_fastapi_instrumentator import Instrumentator

# Expose /metrics endpoint
Instrumentator().instrument(app).expose(app)

# ================== DB Models ==================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    suburb = Column(String)
    property_type = Column(String)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    parking = Column(Integer)
    land_size = Column(Float)
    building_size = Column(Float)
    postcode = Column(String)
    schools_nearby = Column(Integer)
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ================== Helpers ==================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)

def verify_password(pw: str, pw_hash: str) -> bool:
    return pwd_context.verify(pw, pw_hash)

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> User:
    cred_exc = HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise cred_exc
    except JWTError:
        raise cred_exc
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise cred_exc
    return user

# ================== Schemas ==================
class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PredictIn(BaseModel):
    suburb: str
    property_type: str
    bedrooms: int
    bathrooms: int
    parking: int
    land_size: float
    building_size: float
    postcode: str
    schools_nearby: int

class PredictionOut(PredictIn):
    id: int
    price: float
    created_at: datetime

# ================== Auth Endpoints ==================
@app.post("/auth/register", status_code=201)
def register(data: RegisterIn, db=Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(username=data.username, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    return {"msg": "created"}

@app.post("/auth/login", response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# ================== Prediction Logic ==================
def calc_price(inp: PredictIn) -> float:
    base = 500000
    base += inp.bedrooms * 80000 + inp.bathrooms * 60000 + inp.parking * 20000
    base += inp.land_size * 500 + inp.building_size * 1200
    return float(base)

@app.post("/api/predict", response_model=PredictionOut)
def predict(payload: PredictIn, user: User = Depends(get_current_user), db=Depends(get_db)):
    price = calc_price(payload)
    obj = Prediction(price=price, **payload.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return PredictionOut(id=obj.id, price=price, created_at=obj.created_at, **payload.dict())

@app.get("/api/records", response_model=List[PredictionOut])
def list_records(user: User = Depends(get_current_user), db=Depends(get_db)):
    items = db.query(Prediction).order_by(Prediction.id.desc()).all()
    return [
        PredictionOut(
            id=i.id, suburb=i.suburb, property_type=i.property_type, bedrooms=i.bedrooms,
            bathrooms=i.bathrooms, parking=i.parking, land_size=i.land_size,
            building_size=i.building_size, postcode=i.postcode, schools_nearby=i.schools_nearby,
            price=i.price, created_at=i.created_at
        )
        for i in items
    ]

@app.delete("/api/records/{rid}")
def delete_record(rid: int = Path(..., ge=1), user: User = Depends(get_current_user), db=Depends(get_db)):
    row = db.query(Prediction).get(rid)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(row); db.commit()
    return {"deleted": rid}
# ================== Extra Auth Endpoints ==================
@app.get("/auth/me")
def read_me(user: User = Depends(get_current_user)):
    """Return current logged-in user info."""
    return {"username": user.username, "created_at": user.created_at.isoformat()}

# (optional) refresh token nếu cần
@app.post("/auth/refresh", response_model=TokenOut)
def refresh_token(user: User = Depends(get_current_user)):
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


# ================== Prediction Endpoints (unchanged except delete) ==================
@app.post("/api/predict", response_model=PredictionOut)
def predict(payload: PredictIn, user: User = Depends(get_current_user), db=Depends(get_db)):
    price = calc_price(payload)
    obj = Prediction(price=price, **payload.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return PredictionOut(id=obj.id, price=price, created_at=obj.created_at, **payload.dict())

@app.get("/api/records", response_model=List[PredictionOut])
def list_records(user: User = Depends(get_current_user), db=Depends(get_db)):
    items = db.query(Prediction).order_by(Prediction.id.desc()).all()
    return [
        PredictionOut(
            id=i.id, suburb=i.suburb, property_type=i.property_type, bedrooms=i.bedrooms,
            bathrooms=i.bathrooms, parking=i.parking, land_size=i.land_size,
            building_size=i.building_size, postcode=i.postcode, schools_nearby=i.schools_nearby,
            price=i.price, created_at=i.created_at
        )
        for i in items
    ]

@app.delete("/api/records/{rid}")
def delete_record(rid: int = Path(..., ge=1),
                  user: User = Depends(get_current_user),
                  db=Depends(get_db)):
    row = db.query(Prediction).filter(Prediction.id == rid).first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(row); db.commit()
    return {"deleted": rid}