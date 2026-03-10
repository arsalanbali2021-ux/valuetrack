"""
ValueTrack — Authentication Service
Handles user registration, login, and token management.
Uses bcrypt for password hashing.
"""
import bcrypt
import hashlib
import time
import os
from models import User
from db import db_session
from config import Config


def hash_password(password: str) -> str:
    """Hash password with bcrypt (salt rounds from config)."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=Config.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(
        password.encode('utf-8'),
        password_hash.encode('utf-8')
    )


def generate_token(user_id: int) -> str:
    """
    Generate a simple auth token.
    For academic scope — a hash of user_id + timestamp + random bytes.
    In production, use JWT or a proper session framework.
    """
    raw = f"{user_id}:{time.time()}:{os.urandom(16).hex()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def register_user(name: str, email: str, password: str) -> dict:
    """
    Register a new user.
    Returns user dict on success.
    Raises ValueError on validation failure or duplicate email.
    """
    # Validation
    if not name or not name.strip():
        raise ValueError("Name is required")
    if not email or not email.strip():
        raise ValueError("Email is required")
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one number")
    if '@' not in email:
        raise ValueError("Invalid email format")

    email = email.strip().lower()
    name = name.strip()

    # Check duplicate email
    existing = db_session.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("This email is already registered")

    # Create user
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user.to_dict()


def login_user(email: str, password: str) -> dict:
    """
    Authenticate user by email + password.
    Returns dict with user info and token.
    Raises ValueError on invalid credentials.
    """
    if not email or not password:
        raise ValueError("Email and password are required")

    email = email.strip().lower()

    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("Invalid email or password")

    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")

    token = generate_token(user.user_id)

    return {
        'user_id': user.user_id,
        'name': user.name,
        'role': user.role or 'user',
        'monthly_budget': float(user.monthly_budget) if user.monthly_budget is not None else 0.0,
        'token': token
    }


def update_budget(user_id: int, budget: float) -> None:
    user = db_session.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError("User not found")
    user.monthly_budget = budget
    db_session.commit()
