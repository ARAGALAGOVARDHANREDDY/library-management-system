
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


# -------------------------
# BOOKS TABLE
# -------------------------
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    author = Column(String(150), nullable=False)
    category = Column(String(100), nullable=False)

    total_copies = Column(Integer, nullable=False, default=1)
    available_copies = Column(Integer, nullable=False, default=1)

    borrow_records = relationship(
        "BorrowRecord",
        back_populates="book"
    )


# -------------------------
# MEMBERS TABLE
# -------------------------
class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)

    borrow_records = relationship(
        "BorrowRecord",
        back_populates="member"
    )


# -------------------------
# BORROW RECORDS TABLE
# -------------------------
class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, index=True)

    book_id = Column(
        Integer,
        ForeignKey("books.id"),
        nullable=False
    )

    member_id = Column(
        Integer,
        ForeignKey("members.id"),
        nullable=False
    )

    borrowed_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    returned_at = Column(DateTime, nullable=True)

    book = relationship(
        "Book",
        back_populates="borrow_records"
    )

    member = relationship(
        "Member",
        back_populates="borrow_records"
    )


# -------------------------
# USERS TABLE - LOGIN
# -------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(String(255), nullable=False)

    role = Column(
        String(20),
        nullable=False,
        default="student"
    )

    member_id = Column(
        Integer,
        ForeignKey("members.id"),
        unique=True,
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
