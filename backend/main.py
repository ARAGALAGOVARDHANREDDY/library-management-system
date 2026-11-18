
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import engine, Base, get_db

import models
import auth
import books
import members
import borrowing


# Create database tables
Base.metadata.create_all(bind=engine)


# FastAPI application
app = FastAPI(
    title="College Library Management System",
    description="Library Management System Backend API",
    version="2.0.0"
)


# Register all routers
app.include_router(auth.router)
app.include_router(books.router)
app.include_router(members.router)
app.include_router(borrowing.router)


# -------------------------
# HOME
# -------------------------

@app.get("/")
def home():

    return {
        "message": "Welcome to College Library Management System"
    }


# -------------------------
# HEALTH CHECK
# -------------------------

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# -------------------------
# DASHBOARD
# -------------------------

@app.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):

    total_books = db.query(
        func.sum(models.Book.total_copies)
    ).scalar() or 0

    total_members = db.query(
        models.Member
    ).count()

    active_borrowings = db.query(
        models.BorrowRecord
    ).filter(
        models.BorrowRecord.returned_at.is_(None)
    ).count()

    available_books = db.query(
        func.sum(models.Book.available_copies)
    ).scalar() or 0

    return {
        "total_books": total_books,
        "total_members": total_members,
        "active_borrowings": active_borrowings,
        "available_books": available_books
    }
