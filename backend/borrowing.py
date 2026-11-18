
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
import schemas

from database import get_db
from auth import get_current_user


router = APIRouter(
    prefix="/borrowings",
    tags=["Borrowings"]
)


# -----------------------------------
# BORROW BOOK
# -----------------------------------

@router.post(
    "/borrow",
    response_model=schemas.BorrowResponse,
    status_code=201
)
def borrow_book(
    request: schemas.BorrowRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Only students can borrow books
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only students can borrow books."
        )

    # Check whether student has a library membership
    if current_user.member_id is None:
        raise HTTPException(
            status_code=403,
            detail="Your account is not linked to a library membership."
        )

    try:
        # Find book and lock its row
        book = (
            db.query(models.Book)
            .filter(models.Book.id == request.book_id)
            .with_for_update()
            .first()
        )

        if not book:
            raise HTTPException(
                status_code=404,
                detail="Book not found."
            )

        # Find member using logged-in user's member ID
        member = (
            db.query(models.Member)
            .filter(
                models.Member.id == current_user.member_id
            )
            .first()
        )

        if not member:
            raise HTTPException(
                status_code=404,
                detail="Library membership not found."
            )

        # Check book availability
        if book.available_copies <= 0:
            raise HTTPException(
                status_code=400,
                detail="No copies available for this book."
            )

        # Decrease available copies
        book.available_copies -= 1

        # Create borrowing record
        record = models.BorrowRecord(
            book_id=book.id,
            member_id=member.id
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return record

    except Exception:
        db.rollback()
        raise


# -----------------------------------
# ACTIVE BORROWINGS
# -----------------------------------

@router.get(
    "/active",
    response_model=list[schemas.BorrowResponse]
)
def get_active_borrowings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Students can see only their own active borrowings
    query = db.query(models.BorrowRecord).filter(
        models.BorrowRecord.returned_at.is_(None)
    )

    if current_user.role == "student":

        if current_user.member_id is None:
            raise HTTPException(
                status_code=403,
                detail="Library membership not found."
            )

        query = query.filter(
            models.BorrowRecord.member_id == current_user.member_id
        )

    elif current_user.role not in ["admin", "librarian"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission."
        )

    return query.all()


# -----------------------------------
# ALL BORROWING RECORDS
# -----------------------------------

@router.get(
    "/",
    response_model=list[schemas.BorrowResponse]
)
def get_all_borrowings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Students can see only their own records
    if current_user.role == "student":

        if current_user.member_id is None:
            raise HTTPException(
                status_code=403,
                detail="Library membership not found."
            )

        return (
            db.query(models.BorrowRecord)
            .filter(
                models.BorrowRecord.member_id == current_user.member_id
            )
            .all()
        )

    # Admin and librarian can see all records
    if current_user.role in ["admin", "librarian"]:
        return db.query(models.BorrowRecord).all()

    raise HTTPException(
        status_code=403,
        detail="You do not have permission."
    )


# -----------------------------------
# RETURN BOOK
# -----------------------------------

@router.put(
    "/{record_id}/return",
    response_model=schemas.BorrowResponse
)
def return_book(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Only admin and librarian can process returns
    if current_user.role not in ["admin", "librarian"]:
        raise HTTPException(
            status_code=403,
            detail="Only librarians or admins can process book returns."
        )

    try:
        # Find borrowing record and lock it
        record = (
            db.query(models.BorrowRecord)
            .filter(
                models.BorrowRecord.id == record_id
            )
            .with_for_update()
            .first()
        )

        if not record:
            raise HTTPException(
                status_code=404,
                detail="Borrowing record not found."
            )

        if record.returned_at is not None:
            raise HTTPException(
                status_code=400,
                detail="Book has already been returned."
            )

        # Find book and lock it
        book = (
            db.query(models.Book)
            .filter(
                models.Book.id == record.book_id
            )
            .with_for_update()
            .first()
        )

        if not book:
            raise HTTPException(
                status_code=404,
                detail="Book not found."
            )

        # Update return details
        record.returned_at = func.now()

        # Increase available copies
        book.available_copies += 1

        db.commit()
        db.refresh(record)

        return record

    except Exception:
        db.rollback()
        raise
