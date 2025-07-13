from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, validator
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import logging
import re
from typing import List, Optional
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class UserDB(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)


# Pydantic Models
class UserCreate(BaseModel):
    id: str
    name: str
    phone: str
    address: str

    @validator('id')
    def validate_israeli_id(cls, v):
        """Validate Israeli ID using check digit algorithm"""
        if not v.isdigit() or len(v) != 9:
            raise ValueError('ID must be exactly 9 digits')

        # Israeli ID validation algorithm
        id_digits = [int(d) for d in v]
        check_sum = 0

        for i, digit in enumerate(id_digits[:-1]):  # All digits except last (check digit)
            if i % 2 == 0:  # Even position (0-indexed) - multiply by 1
                check_sum += digit
            else:  # Odd position (1-indexed) - multiply by 2
                doubled = digit * 2
                # If result is two digits, add them together
                check_sum += doubled if doubled < 10 else (doubled // 10) + (doubled % 10)

        # Calculate what the check digit should be
        remainder = check_sum % 10
        calculated_check_digit = (10 - remainder) % 10

        actual_check_digit = id_digits[-1]
        if calculated_check_digit != actual_check_digit:
            raise ValueError(
                f'Invalid Israeli ID - check digit should be {calculated_check_digit}, got {actual_check_digit}')

        return v

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        # Allow formats like +972-50-1234567, +1-555-123-4567, etc.
        phone_pattern = r'^\+[1-9]\d{1,14}$|^\+[1-9]\d{0,3}-\d{2,4}-\d{6,7}$'
        if not re.match(phone_pattern, v):
            raise ValueError('Phone number must be in international format (e.g., +972501234567 or +972-50-1234567)')
        return v

    @validator('name')
    def validate_name(cls, v):
        """Validate name is not empty"""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    @validator('address')
    def validate_address(cls, v):
        """Validate address is not empty"""
        if not v or not v.strip():
            raise ValueError('Address cannot be empty')
        return v.strip()


class UserResponse(BaseModel):
    id: str
    name: str
    phone: str
    address: str
    created_at: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str


class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
    timestamp: datetime


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("User Management API server starting up...")
    yield
    # Shutdown
    logger.info("User Management API server shutting down...")


# FastAPI app
app = FastAPI(
    title="User Management API",
    description="REST API for managing users with Israeli ID validation",
    version="1.0.0",
    lifespan=lifespan
)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    from fastapi.responses import JSONResponse

    # Convert validation errors to serializable format
    serializable_errors = []
    for error in exc.errors():
        serializable_error = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": error.get("input")
        }
        serializable_errors.append(serializable_error)

    logger.error(f"Validation error: {serializable_errors}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "details": serializable_errors,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    from fastapi.responses import JSONResponse
    import traceback
    error_details = traceback.format_exc()
    logger.error(f"Unexpected error: {str(exc)}")
    logger.error(f"Traceback: {error_details}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# API Endpoints
@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    logger.info(f"Attempting to create user with ID: {user.id}")

    # Check if user already exists
    existing_user = db.query(UserDB).filter(UserDB.id == user.id).first()
    if existing_user:
        logger.warning(f"User with ID {user.id} already exists")
        raise HTTPException(status_code=409, detail="User with this ID already exists")

    # Create new user
    try:
        db_user = UserDB(
            id=user.id,
            name=user.name,
            phone=user.phone,
            address=user.address
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"Successfully created user with ID: {user.id}")
        return db_user

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create user")


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID"""
    logger.info(f"Fetching user with ID: {user_id}")

    # Validate ID format
    if not user_id.isdigit() or len(user_id) != 9:
        logger.warning(f"Invalid ID format: {user_id}")
        raise HTTPException(status_code=400, detail="ID must be exactly 9 digits")

    try:
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user:
            logger.warning(f"User with ID {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")

        logger.info(f"Successfully retrieved user with ID: {user_id}")
        return user

    except HTTPException:
        # Re-raise HTTP exceptions (like 404, 400)
        raise
    except Exception as e:
        logger.error(f"Database error while fetching user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/users", response_model=List[str])
async def list_users(db: Session = Depends(get_db)):
    """List all user IDs"""
    logger.info("Fetching all user IDs")

    user_ids = db.query(UserDB.id).all()
    user_ids_list = [user_id[0] for user_id in user_ids]

    logger.info(f"Retrieved {len(user_ids_list)} user IDs")
    return user_ids_list


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)