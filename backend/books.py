
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas

from database import get_db
from auth import require_roles


router = APIRouter(
    prefix="/books",
    tags=["Books"]
)


# =====================================
# ADD BOOK
# Librarian and Admin only
# =====================================

@router.post(
    "/",
    response_model=schemas.BookResponse,
    status_code=201
)
def create_book(
    request: schemas.BookCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("admin", "librarian")
    )
):

    new_book = models.Book(
        title=request.title,
        author=request.author,
        category=request.category,
        total_copies=request.total_copies,
        available_copies=request.total_copies
    )

    try:
        db.add(new_book)
        db.commit()
        db.refresh(new_book)

        return new_book

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to add book."
        )


# =====================================
# GET ALL BOOKS
# Public access
# =====================================

@router.get(
    "/",
    response_model=list[schemas.BookResponse]
)
def get_books(
    db: Session = Depends(get_db)
):

    return db.query(models.Book).all()


# =====================================
# SEARCH BOOKS BY TITLE
# Public access
# =====================================

@router.get(
    "/search",
    response_model=list[schemas.BookResponse]
)
def search_books(
    title: str,
    db: Session = Depends(get_db)
):

    return (
        db.query(models.Book)
        .filter(
            models.Book.title.ilike(f"%{title}%")
        )
        .all()
    )


# =====================================
# GET BOOK BY ID
# Public access
# =====================================

@router.get(
    "/{book_id}",
    response_model=schemas.BookResponse
)
def get_book(
    book_id: int,
    db: Session = Depends(get_db)
):

    book = (
        db.query(models.Book)
        .filter(models.Book.id == book_id)
        .first()
    )

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found."
        )

    return book


# =====================================
# UPDATE BOOK
# Librarian and Admin only
# =====================================

@router.put(
    "/{book_id}",
    response_model=schemas.BookResponse
)
def update_book(
    book_id: int,
    request: schemas.BookUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("admin", "librarian")
    )
):

    book = (
        db.query(models.Book)
        .filter(models.Book.id == book_id)
        .first()
    )

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found."
        )

    data = request.model_dump(exclude_unset=True)

    # Update total copies safely
    if "total_copies" in data and data["total_copies"] is not None:

        issued_copies = (
            book.total_copies - book.available_copies
        )

        if data["total_copies"] < issued_copies:
            raise HTTPException(
                status_code=400,
                detail="Total copies cannot be less than issued copies."
            )

        if data["total_copies"] < 0:
            raise HTTPException(
                status_code=400,
                detail="Total copies cannot be negative."
            )

        book.total_copies = data["total_copies"]

        book.available_copies = (
            data["total_copies"] - issued_copies
        )

    # Update other book details
    for field in ["title", "author", "category"]:

        if field in data and data[field] is not None:
            setattr(book, field, data[field])

    try:
        db.commit()
        db.refresh(book)

        return book

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update book."
        )


# =====================================
# DELETE BOOK
# Admin only
# =====================================

@router.delete("/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("admin")
    )
):

    book = (
        db.query(models.Book)
        .filter(models.Book.id == book_id)
        .first()
    )

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found."
        )

    # Check borrowing history
    history = (
        db.query(models.BorrowRecord)
        .filter(models.BorrowRecord.book_id == book_id)
        .first()
    )

    if history:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a book with borrowing history."
        )

    try:
        db.delete(book)
        db.commit()

        return {
            "message": "Book deleted successfully."
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete book."
        )
